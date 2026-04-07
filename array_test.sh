#!/bin/bash
#
#SBATCH --job-name="test_array"
#SBATCH --time=04:00:00
#SBATCH --partition=compute
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=3968MB
#SBATCH --account=education-eemcs-msc-cs
#SBATCH --array=[1150, 1151, 1152, 1153, 1154, 1170, 1171, 1172, 1173, 1174, 1175, 1176, 1177, 1178, 1179, 1180, 1181, 1182, 1183, 1184, 1185, 1186, 1187, 1188, 1189, 1195, 1196, 1197, 1198, 1199, 1240, 1241, 1242, 1243, 1244, 1250, 1251, 1252, 1253, 1254, 1260, 1261, 1262, 1263, 1264, 1265, 1266, 1267, 1268, 1269, 1270, 1271, 1272, 1273, 1274, 1275, 1276, 1277, 1278, 1279, 1280, 1281, 1282, 1283, 1284, 1285, 1286, 1287, 1288, 1289, 1290, 1291, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300, 1301, 1302, 1303, 1304, 1305, 1306, 1307, 1308, 1309, 1310, 1311, 1312, 1313, 1314, 1315, 1316, 1317, 1318, 1319, 1320, 1321, 1322, 1323, 1324, 1330, 1331, 1332, 1333, 1334, 1335, 1336, 1337, 1338, 1339, 1345, 1346, 1347, 1348, 1349, 1360, 1361, 1362, 1363, 1364, 1370, 1371, 1372, 1373, 1374, 1375, 1376, 1377, 1378, 1379]

#SBATCH --output=logs/out_%A_%a.txt
#SBATCH --error=logs/err_%A_%a.txt

module load 2025
module load python
module load gurobi/12.0.0
module load pyomo

cd /home/thomasverwaal/Robust-Rail-NL/mathematical-models
source ~/pyomo_project/env/bin/activate

srun python3 experiments_cluster.py