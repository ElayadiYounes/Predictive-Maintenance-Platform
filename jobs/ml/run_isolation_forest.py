from jobs.common.logger import logger

from jobs.ml.readers.gold_reader import read_gold_table
from jobs.ml.features.inspection_features import InspectionFeatureEngineering
from jobs.ml.models.isolation_forest import InspectionIsolationForest
from jobs.ml.validation.anomaly_validator import InspectionAnomalyValidator
from jobs.ml.writer.anomaly_writer import AnomalyWriter
from jobs.ml.catalog.ml_catalog import AnomalyCatalog
#from jobs.ml.splitters.temporal_split import TemporalTrainTestSplitter

def run_isolation_forest():
    """
        Orchestre l'ensemble du pipeline ML Isolation Forest.

        Pipeline
        --------
        Gold fact_inspection
                ↓
            Gold Reader
                ↓
        Feature Engineering
                ↓
          Isolation Forest
                ↓
            Validation
                ↓
            ML Writer
                ├── fact_inspection_anomaly → Gold
                └── modèle entraîné       → Models
        """
    logger.info("=" * 80)
    logger.info("ISOLATION FOREST ML PIPELINE START")
    logger.info("=" * 80)

    try:
        #lecture table gold
        logger.info("Etape 1/6 : Lecture de Fact_Inspection et dim_time")
        dataframe = read_gold_table(table_name="fact_inspection")
        logger.info(f"fact_inspection chargée : {len(dataframe):,} lignes.")

        logger.info("Lecture de dim_time pour récupérer la date...")
        #dim_time = read_gold_table(table_name="dim_time")

        #dataframe = dataframe.merge(
        #    dim_time[["id_time", "date"]],
        #    on="id_time",
        #    how="left",
        #    validate="many_to_one",
        #)

        #logger.info("Date ajoutée à fact_inspection.")

        #feature Engineering
        logger.info("Etape 2/6 : Construction des Features ...")
        feature_engineering = InspectionFeatureEngineering()
        features = feature_engineering.build_feature_engineering(dataframe)
        logger.info(f"DataSet ML construit : {len(features):,} lignes.")

        feature_columns = feature_engineering.FEATURE_COLUMNS
        logger.info(f"Nombre de features utilisées : {len(feature_columns)}")
        logger.info(f"Features Isolation Forest : {feature_columns}")

        logger.info("Etape 3/6 : Split temporel Train/Test...")

        #splitter = TemporalTrainTestSplitter(
        #    test_ratio=0.20,
        #    min_train_samples=5,
        #    min_test_samples=1,
        #)

        #train_data, test_data = splitter.split(features)

        #logger.info(
        #    f"Train : {len(train_data):,} lignes | "
        #    f"Test : {len(test_data):,} lignes."
        #)


        #entrainement
        logger.info("Etape 4/6 : Entraînement Isolation Forest...")
        isolation_forest = InspectionIsolationForest(
            n_estimators=200,
            contamination="auto",
            random_state=42,
            min_samples_dedicated=30,
        )

        logger.info("Entraînement modèle Global ...")
        isolation_forest.train_global(dataframe=features, feature_columns=feature_columns)

        logger.info("Entraînement modèle dèdiès ...")
        dedicated_models = (
            isolation_forest.train_dedicated_models(dataframe=features)
        )
        logger.info(f"Nombre de modèles dédiés : {len(dedicated_models)}.")

        logger.info("Détection des Anomalies ...")
        ml_results = isolation_forest.predict(dataframe=features)

        alert_columns = feature_engineering.CONTEXT_COLUMNS
        dataframe_anomalys = ml_results.merge(
            features[alert_columns],
            on=["id_inspection", "id_equipement"],
            how="left",
            validate="one_to_one",
        )
        logger.info(f"Résultats générés : " f"{len(dataframe_anomalys):,} lignes.")


        logger.info("Etape 5/6 : Validation Isolation Forest...")
        validator = InspectionAnomalyValidator()
        dataframe_anomalys = validator.validate(dataframe=dataframe_anomalys)

        #écriture des anomalies + models

        logger.info("Etape 6/6 : Ecriture Isolation Forest ET modèles entrainées ...")
        writer = AnomalyWriter()

        logger.info("Sauvegarde de fact_inspection_anomaly...")

        writer.write_anomaly_results(dataframe=dataframe_anomalys)
        logger.info("Enregistrement de fact_inspection_anomaly dans le catalogue Hive...")
        catalog = AnomalyCatalog()
        catalog.register_anomaly_table()
        logger.success("fact_inspection_anomaly enregistrée " "dans le catalogue Hive.")

        if isolation_forest.global_model is None:
            raise ValueError("LE modèle global Isolation Forest n'est pas disponible")

        logger.info("sauvegarde du modèle global ...")
        writer.write_anomaly_model(
            model=isolation_forest.global_model,
            model_name="isolation_forest",
            model_version="v1",
            model_type="global",
        )

        dedicated_models = isolation_forest.dedicated_models
        logger.info(f"Nomber de modèles dédiès à sauvegarder : {len(dedicated_models)}")

        for id_equipement, model in dedicated_models.items():
            if model is None :
                logger.warning(f"Modèle dédié absent pour l'équipement : {id_equipement} => Sauvegarde ignorée")
                continue

            logger.info(f"Sauvegarde du modèle dédie pour l'équipement {id_equipement} ...")
            writer.write_anomaly_model(
                model=model,
                model_name="isolation_forest",
                model_version="v1",
                model_type="equipment",
                id_equipement=id_equipement,
            )


        logger.success("Tous les modèles Isolation Forest ont été sauvegardés avec succès.")

    except Exception :
        logger.exception( "Le pipeline Machine Learning des inspections a échoué." )
        raise


if __name__ == "__main__" :
    run_isolation_forest()


