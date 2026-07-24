Write-Host ""
Write-Host "==========================================="
Write-Host "Downloading Third Party Dependencies"
Write-Host "==========================================="
Write-Host ""

New-Item aws -ItemType Directory -Force | Out-Null
New-Item postgres -ItemType Directory -Force | Out-Null
New-Item spark -ItemType Directory -Force | Out-Null
New-Item hive -ItemType Directory -Force | Out-Null
New-Item hadoop -ItemType Directory -Force | Out-Null

Write-Host "Downloading Spark..."

Invoke-WebRequest `
https://archive.apache.org/dist/spark/spark-3.5.2/spark-3.5.2-bin-hadoop3.tgz `
-OutFile spark/spark-3.5.2-bin-hadoop3.tgz

Write-Host "Downloading Hadoop..."

Invoke-WebRequest `
https://archive.apache.org/dist/hadoop/common/hadoop-3.3.4/hadoop-3.3.4.tar.gz `
-OutFile hadoop/hadoop-3.3.4.tar.gz

Write-Host "Downloading Hive..."

Invoke-WebRequest `
https://archive.apache.org/dist/hive/hive-3.1.3/apache-hive-3.1.3-bin.tar.gz `
-OutFile hive/apache-hive-3.1.3-bin.tar.gz

Write-Host "Downloading PostgreSQL JDBC Driver..."

Invoke-WebRequest `
https://jdbc.postgresql.org/download/postgresql-42.7.7.jar `
-OutFile postgres/postgresql-42.7.7.jar

Write-Host "Downloading Hadoop AWS..."

Invoke-WebRequest `
https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar `
-OutFile aws/hadoop-aws-3.3.4.jar

Write-Host "Downloading AWS SDK Bundle..."

Invoke-WebRequest `
https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar `
-OutFile aws/aws-java-sdk-bundle-1.12.262.jar

Write-Host ""
Write-Host "Done."