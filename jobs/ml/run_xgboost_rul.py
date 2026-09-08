from jobs.common.logger import logger

# Extraction et Utilitaires partagés
from jobs.ml.readers.gold_reader import read_gold_table
from jobs.ml.splitters.temporal_split import TemporalTrainTestSplitter


from jobs.ml.features.xgboost_features import RULFeatureEngineering
from jobs.ml.models.xgboot_rul import InspectionXGBoostRUL
from jobs.ml.validation.rul_validator import RULResultsValidator
from jobs.ml.writer.rul_writer import RULWriter
from jobs.ml.catalog.ml_catalog import RULCatalog


def run_xgboost_rul():
    """
    Orchestre l'ensemble du pipeline Machine Learning XGBoost pour la RUL.

    Pipeline de Production
    ----------------------
    Étape 1 : Lecture & Fusion complète (Anomalies + Mesures physiques + Dates)
    Étape 2 : Feature Engineering (Signatures vibratoires + Compte à rebours RUL)
    Étape 3 : Découpage temporel Train/Test (80% / 20%) par équipement
    Étape 4 : [PHASE 1] Apprentissage sur TRAIN et Validation sur TEST (Calcul MAE)
    Étape 5 : [PHASE 2] Entraînement final du modèle de Production sur 100%
    Étape 6 : Sauvegarde dans le Data Lake (Gold & Models) et Catalogue Hive SQL
    """
    logger.info("=" * 80)
    logger.info("XGBOOST RUL REGRESSION ML PIPELINE START")
    logger.info("=" * 80)

    try:
        # ============================================================
        # ÉTAPE 1/6 : Lecture et Fusion des Données Gold
        # ============================================================
        logger.info("Etape 1/6 : Lecture des tables fact_inspection_anomaly, fact_inspection et dim_time")

        df_anomalies = read_gold_table(table_name="fact_inspection_anomaly")
        df_fact = read_gold_table(table_name="fact_inspection")
        df_time = read_gold_table(table_name="dim_time")

        logger.info("Chaînage des jointures pour consolider l'axe chronologique réel...")

        cles_communes = [
            "id_inspection",
            "id_equipement",
            "alert_temperature",
            "alert_vib_axiale",
            "alert_vib_horiz",
            "alert_vib_vert"
        ]

        # 1ère jointure : Croisement des résultats de l'IA (scores) avec les mesures physiques brutes
        df_merged = df_anomalies.merge(
            df_fact,
            on=cles_communes,
            how="inner"
        )

        # 2ème jointure : Récupération de la vraie date physique d'inspection (dim_time)
        dataframe_complet = df_merged.merge(
            df_time[["id_time", "date"]],
            on="id_time",
            how="left"
        )
        logger.info(f"Données brutes consolidées : {len(dataframe_complet):,} lignes.")

        # ============================================================
        # ÉTAPE 2/6 : RUL Feature Engineering
        # ============================================================
        logger.info("Etape 2/6 : Construction des Features et calcul de la cible target_rul...")

        feature_engineering = RULFeatureEngineering(max_rul_days=30)
        features = feature_engineering.build_feature_engineering(dataframe_complet)

        feature_columns = feature_engineering.FEATURE_COLUMNS
        logger.info(f"Dataset ML construit : {len(features):,} lignes exploitables.")
        logger.info(f"Nombre de features actives pour XGBoost : {len(feature_columns)}")
        logger.info(f"Périmètre des features : {feature_columns}")

        # ============================================================
        # ÉTAPE 3/6 : Split Temporel pour l'Évaluation de Sécurité
        # ============================================================
        logger.info("Etape 3/6 : Séparation temporelle Train/Test par Équipement...")

        splitter = TemporalTrainTestSplitter(
            test_ratio=0.20,
            min_train_samples=5,
            min_test_samples=1,
        )
        train_data, test_data = splitter.split(features)
        logger.info(f"Train set : {len(train_data):,} lignes | Test set : {len(test_data):,} lignes.")

        # ============================================================
        # ÉTAPE 4/6 : Phase 1 - Évaluation de la Précision du Modèle (Test Set)
        # ============================================================
        logger.info("Etape 4/6 : [PHASE 1] Entraînement et évaluation sur le jeu de TEST...")

        evaluation_model = InspectionXGBoostRUL(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )

        # Apprentissage sur le passé isolé
        evaluation_model.train(dataframe=train_data, feature_columns=feature_columns)

        # Inférence sur le futur isolé (Test)
        evaluation_results = evaluation_model.predict(dataframe=test_data)

        # Analyse descriptive et calcul des métriques d'erreurs (MAE / Statuts de fenêtres)
        logger.info("Analyse de la précision temporelle du modèle d'évaluation...")
        results_validator = RULResultsValidator(safe_error_window_days=1)
        results_validator.validate(dataframe=evaluation_results)

        logger.success("Phase 1 validée : Performance jugée robuste. Passage au modèle final.")

        # ============================================================
        # ÉTAPE 5/6 : Phase 2 - Entraînement de Production (100% Historique)
        # ============================================================
        logger.info("Etape 5/6 : [PHASE 2] Entraînement du modèle final de Production sur 100% des données...")

        production_model = InspectionXGBoostRUL(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )

        # Entraînement complet (Modèle Unique Global)
        production_model.train(dataframe=features, feature_columns=feature_columns)

        # Inférence globale sur 100% des lignes pour remplir l'historique de votre Dashboard
        logger.info("Génération des prédictions de RUL historiques complètes...")
        production_results = production_model.predict(dataframe=features)

        # Enrichissement final des données de production avec les indicateurs d'écarts
        production_results = results_validator.validate(dataframe=production_results)

        # ============================================================
        # ÉTAPE 6/6 : Écriture S3 (Gold & Models) & Enregistrement Hive
        # ============================================================
        logger.info("Etape 6/6 : Sauvegarde des résultats, des modèles et catalogue Hive...")
        rul_writer = RULWriter()

        # 1. Écriture de la table Gold fact_inspection_rul
        logger.info("Sauvegarde de la table fact_inspection_rul dans le bucket Gold...")
        rul_writer.write_rul_results(dataframe=production_results)

        # 2. Déclaration au catalogue Hive via Spark Thrift Server
        logger.info("Enregistrement de la table RUL dans le catalogue Hive...")
        catalog = RULCatalog()
        catalog.register_rul_table()
        logger.success("Table fact_inspection_rul enregistrée et synchronisée.")

        # 3. Sauvegarde du fichier binaire du modèle (.joblib)
        if production_model.global_model is None:
            raise ValueError("Le modèle global XGBoost de production n'est pas disponible.")

        logger.info("Sauvegarde du fichier binaire du modèle dans le bucket Models...")
        rul_writer.write_rul_model(
            model=production_model.global_model,
            model_name="xgboost_rul",
            model_version="v1",
            model_type="global"
        )

        logger.success("=" * 80)
        logger.success("XGBOOST RUL REGRESSION PIPELINE EXÉCUTÉ AVEC SUCCÈS À 100% !")
        logger.success("=" * 80)

    except Exception:
        logger.exception("Échec critique du pipeline Machine Learning XGBoost RUL.")
        raise


if __name__ == "__main__":
    run_xgboost_rul()
