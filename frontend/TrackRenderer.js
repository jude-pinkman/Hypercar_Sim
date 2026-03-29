/**
 * TrackRenderer.js — F1 Circuit Map Renderer
 *
 * Albert Park (AUS): renders the OFFICIAL SVG map directly onto the canvas
 * as a background image, then draws car markers on top.
 * This gives pixel-perfect rendering matching the official circuit diagram.
 *
 * Other circuits: polyline rendering from coordinate arrays.
 *
 * Car marker positions use arc-length-sampled centreline points (AUS_TRACK_POINTS).
 */

// ─── Albert Park centreline points (300 arc-length-sampled from path1559 subpath1)
// Used ONLY for car marker positioning — the visual is from the SVG image
const AUS_TRACK_POINTS = [{"x":524.29,"y":758.35,"sector":1,"drsZone":false,"pitLane":true,"corner":0},{"x":518.05,"y":749.07,"sector":1,"drsZone":false,"pitLane":true,"corner":0},{"x":516.46,"y":737.84,"sector":1,"drsZone":false,"pitLane":true,"corner":0},{"x":516.17,"y":726.47,"sector":1,"drsZone":false,"pitLane":true,"corner":0},{"x":513.7,"y":715.46,"sector":1,"drsZone":false,"pitLane":true,"corner":0},{"x":507.43,"y":706.0,"sector":1,"drsZone":false,"pitLane":true,"corner":0},{"x":499.63,"y":697.73,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":490.84,"y":690.53,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":480.96,"y":684.93,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":470.21,"y":681.24,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":459.11,"y":678.77,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":447.87,"y":677.05,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":436.56,"y":675.81,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":425.24,"y":674.69,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":413.96,"y":673.23,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":402.72,"y":671.49,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":391.51,"y":669.58,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":380.32,"y":667.52,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":369.16,"y":665.36,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":358.0,"y":663.11,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":346.87,"y":660.8,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":335.74,"y":658.42,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":324.63,"y":656.01,"sector":1,"drsZone":false,"pitLane":false,"corner":16},{"x":313.52,"y":653.54,"sector":1,"drsZone":false,"pitLane":false,"corner":16},{"x":302.45,"y":650.91,"sector":1,"drsZone":false,"pitLane":false,"corner":16},{"x":291.47,"y":647.96,"sector":1,"drsZone":false,"pitLane":false,"corner":16},{"x":280.61,"y":644.57,"sector":1,"drsZone":false,"pitLane":false,"corner":16},{"x":269.86,"y":640.86,"sector":1,"drsZone":false,"pitLane":false,"corner":16},{"x":259.18,"y":636.96,"sector":1,"drsZone":false,"pitLane":false,"corner":16},{"x":248.52,"y":632.98,"sector":1,"drsZone":false,"pitLane":false,"corner":16},{"x":237.88,"y":628.96,"sector":1,"drsZone":false,"pitLane":false,"corner":16},{"x":227.24,"y":624.93,"sector":1,"drsZone":false,"pitLane":false,"corner":16},{"x":216.61,"y":620.88,"sector":1,"drsZone":false,"pitLane":false,"corner":16},{"x":206.01,"y":616.75,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":195.47,"y":612.47,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":185.04,"y":607.95,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":174.71,"y":603.17,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":164.45,"y":598.26,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":154.26,"y":593.22,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":144.21,"y":587.88,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":134.69,"y":581.68,"sector":1,"drsZone":false,"pitLane":false,"corner":15},{"x":127.88,"y":572.7,"sector":1,"drsZone":false,"pitLane":false,"corner":15},{"x":127.54,"y":561.58,"sector":1,"drsZone":false,"pitLane":false,"corner":15},{"x":132.53,"y":551.42,"sector":1,"drsZone":false,"pitLane":false,"corner":15},{"x":139.1,"y":542.14,"sector":1,"drsZone":false,"pitLane":false,"corner":15},{"x":145.81,"y":532.95,"sector":1,"drsZone":false,"pitLane":false,"corner":15},{"x":152.38,"y":523.67,"sector":1,"drsZone":false,"pitLane":false,"corner":15},{"x":158.63,"y":514.17,"sector":1,"drsZone":false,"pitLane":false,"corner":15},{"x":163.95,"y":504.12,"sector":1,"drsZone":false,"pitLane":false,"corner":15},{"x":165.95,"y":493.02,"sector":1,"drsZone":false,"pitLane":false,"corner":15},{"x":164.97,"y":481.71,"sector":1,"drsZone":false,"pitLane":false,"corner":15},{"x":161.46,"y":470.92,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":155.4,"y":461.31,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":148.66,"y":452.15,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":141.74,"y":443.12,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":134.76,"y":434.13,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":127.77,"y":425.17,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":120.78,"y":416.19,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":113.84,"y":407.17,"sector":1,"drsZone":false,"pitLane":false,"corner":14},{"x":106.99,"y":398.1,"sector":1,"drsZone":false,"pitLane":false,"corner":14},{"x":100.96,"y":388.5,"sector":1,"drsZone":false,"pitLane":false,"corner":14},{"x":99.36,"y":377.33,"sector":1,"drsZone":false,"pitLane":false,"corner":14},{"x":100.89,"y":366.07,"sector":1,"drsZone":false,"pitLane":false,"corner":14},{"x":103.47,"y":354.99,"sector":1,"drsZone":false,"pitLane":false,"corner":14},{"x":106.41,"y":344.0,"sector":1,"drsZone":false,"pitLane":false,"corner":14},{"x":109.51,"y":333.06,"sector":1,"drsZone":false,"pitLane":false,"corner":14},{"x":112.76,"y":322.16,"sector":1,"drsZone":false,"pitLane":false,"corner":14},{"x":116.2,"y":311.31,"sector":1,"drsZone":false,"pitLane":false,"corner":14},{"x":119.84,"y":300.54,"sector":1,"drsZone":false,"pitLane":false,"corner":14},{"x":123.78,"y":289.87,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":128.3,"y":279.44,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":133.83,"y":269.5,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":139.82,"y":259.83,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":146.08,"y":250.33,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":152.56,"y":240.99,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":159.28,"y":231.81,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":166.13,"y":222.72,"sector":1,"drsZone":false,"pitLane":false,"corner":13},{"x":172.77,"y":213.49,"sector":1,"drsZone":false,"pitLane":false,"corner":13},{"x":178.81,"y":203.85,"sector":1,"drsZone":false,"pitLane":false,"corner":13},{"x":184.04,"y":193.76,"sector":1,"drsZone":false,"pitLane":false,"corner":13},{"x":188.76,"y":183.41,"sector":1,"drsZone":false,"pitLane":false,"corner":13},{"x":193.27,"y":172.96,"sector":1,"drsZone":false,"pitLane":false,"corner":13},{"x":197.7,"y":162.49,"sector":1,"drsZone":false,"pitLane":false,"corner":13},{"x":202.21,"y":152.05,"sector":1,"drsZone":false,"pitLane":false,"corner":13},{"x":207.31,"y":141.88,"sector":1,"drsZone":false,"pitLane":false,"corner":13},{"x":214.84,"y":133.5,"sector":1,"drsZone":false,"pitLane":false,"corner":13},{"x":225.39,"y":129.65,"sector":1,"drsZone":false,"pitLane":false,"corner":13},{"x":236.69,"y":130.58,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":248.01,"y":131.63,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":259.36,"y":131.07,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":270.57,"y":129.15,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":281.5,"y":126.04,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":292.03,"y":121.75,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":302.06,"y":116.39,"sector":1,"drsZone":false,"pitLane":false,"corner":0},{"x":311.86,"y":110.63,"sector":1,"drsZone":false,"pitLane":false,"corner":12},{"x":321.83,"y":105.15,"sector":1,"drsZone":false,"pitLane":false,"corner":12},{"x":332.26,"y":100.65,"sector":1,"drsZone":false,"pitLane":false,"corner":12},{"x":343.3,"y":97.94,"sector":1,"drsZone":false,"pitLane":false,"corner":12},{"x":354.54,"y":96.17,"sector":1,"drsZone":false,"pitLane":false,"corner":12},{"x":365.85,"y":94.97,"sector":2,"drsZone":false,"pitLane":false,"corner":12},{"x":377.21,"y":94.51,"sector":2,"drsZone":false,"pitLane":false,"corner":12},{"x":388.57,"y":94.94,"sector":2,"drsZone":false,"pitLane":false,"corner":12},{"x":399.86,"y":96.35,"sector":2,"drsZone":false,"pitLane":false,"corner":12},{"x":410.98,"y":98.74,"sector":2,"drsZone":false,"pitLane":false,"corner":12},{"x":421.86,"y":102.04,"sector":2,"drsZone":false,"pitLane":false,"corner":12},{"x":432.25,"y":106.63,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":441.99,"y":112.51,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":451.26,"y":119.1,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":460.27,"y":126.04,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":469.04,"y":133.28,"sector":2,"drsZone":false,"pitLane":false,"corner":11},{"x":477.6,"y":140.77,"sector":2,"drsZone":false,"pitLane":false,"corner":11},{"x":486.0,"y":148.44,"sector":2,"drsZone":false,"pitLane":false,"corner":11},{"x":494.29,"y":156.23,"sector":2,"drsZone":false,"pitLane":false,"corner":11},{"x":502.51,"y":164.09,"sector":2,"drsZone":false,"pitLane":false,"corner":11},{"x":510.69,"y":171.99,"sector":2,"drsZone":false,"pitLane":false,"corner":11},{"x":518.86,"y":179.91,"sector":2,"drsZone":false,"pitLane":false,"corner":11},{"x":526.97,"y":187.89,"sector":2,"drsZone":false,"pitLane":false,"corner":11},{"x":534.95,"y":196.0,"sector":2,"drsZone":false,"pitLane":false,"corner":11},{"x":542.94,"y":204.08,"sector":2,"drsZone":false,"pitLane":false,"corner":11},{"x":550.69,"y":212.39,"sector":2,"drsZone":false,"pitLane":false,"corner":11},{"x":557.32,"y":221.62,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":562.93,"y":231.5,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":566.68,"y":242.23,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":568.29,"y":253.45,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":568.17,"y":264.83,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":568.45,"y":276.2,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":568.79,"y":287.57,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":569.77,"y":298.9,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":571.54,"y":310.13,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":574.49,"y":321.11,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":577.62,"y":332.05,"sector":2,"drsZone":false,"pitLane":false,"corner":10},{"x":581.02,"y":342.9,"sector":2,"drsZone":false,"pitLane":false,"corner":10},{"x":584.78,"y":353.64,"sector":2,"drsZone":false,"pitLane":false,"corner":10},{"x":588.69,"y":364.32,"sector":2,"drsZone":false,"pitLane":false,"corner":10},{"x":592.94,"y":374.86,"sector":2,"drsZone":false,"pitLane":false,"corner":10},{"x":597.99,"y":385.05,"sector":2,"drsZone":false,"pitLane":false,"corner":10},{"x":603.15,"y":395.19,"sector":2,"drsZone":false,"pitLane":false,"corner":10},{"x":608.44,"y":405.26,"sector":2,"drsZone":false,"pitLane":false,"corner":10},{"x":613.91,"y":415.23,"sector":2,"drsZone":false,"pitLane":false,"corner":10},{"x":619.64,"y":425.06,"sector":2,"drsZone":false,"pitLane":false,"corner":10},{"x":625.7,"y":434.68,"sector":2,"drsZone":false,"pitLane":false,"corner":10},{"x":632.21,"y":444.01,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":639.31,"y":452.89,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":647.02,"y":461.25,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":655.23,"y":469.12,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":663.79,"y":476.62,"sector":2,"drsZone":false,"pitLane":false,"corner":9},{"x":672.64,"y":483.75,"sector":2,"drsZone":false,"pitLane":false,"corner":9},{"x":681.78,"y":490.52,"sector":2,"drsZone":false,"pitLane":false,"corner":9},{"x":691.25,"y":496.82,"sector":2,"drsZone":false,"pitLane":false,"corner":9},{"x":701.2,"y":502.32,"sector":2,"drsZone":false,"pitLane":false,"corner":9},{"x":711.47,"y":507.23,"sector":2,"drsZone":false,"pitLane":false,"corner":9},{"x":721.8,"y":511.99,"sector":2,"drsZone":false,"pitLane":false,"corner":9},{"x":732.27,"y":516.43,"sector":2,"drsZone":false,"pitLane":false,"corner":9},{"x":742.98,"y":520.24,"sector":2,"drsZone":false,"pitLane":false,"corner":9},{"x":753.95,"y":523.22,"sector":2,"drsZone":false,"pitLane":false,"corner":9},{"x":765.1,"y":525.47,"sector":2,"drsZone":false,"pitLane":false,"corner":9},{"x":776.32,"y":527.35,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":787.56,"y":529.09,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":798.82,"y":530.74,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":810.1,"y":532.22,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":821.41,"y":533.42,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":832.74,"y":534.36,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":844.09,"y":535.12,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":855.45,"y":535.8,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":866.8,"y":536.43,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":878.17,"y":536.93,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":889.54,"y":537.15,"sector":2,"drsZone":false,"pitLane":false,"corner":8},{"x":899.14,"y":532.32,"sector":2,"drsZone":false,"pitLane":false,"corner":8},{"x":906.9,"y":524.0,"sector":2,"drsZone":false,"pitLane":false,"corner":8},{"x":915.01,"y":516.02,"sector":2,"drsZone":false,"pitLane":false,"corner":8},{"x":923.33,"y":508.27,"sector":2,"drsZone":false,"pitLane":false,"corner":8},{"x":931.77,"y":500.64,"sector":2,"drsZone":false,"pitLane":false,"corner":8},{"x":940.37,"y":493.19,"sector":2,"drsZone":false,"pitLane":false,"corner":8},{"x":949.64,"y":486.67,"sector":2,"drsZone":false,"pitLane":false,"corner":8},{"x":960.87,"y":485.6,"sector":2,"drsZone":false,"pitLane":false,"corner":8},{"x":972.21,"y":486.5,"sector":2,"drsZone":false,"pitLane":false,"corner":8},{"x":983.54,"y":487.47,"sector":2,"drsZone":false,"pitLane":false,"corner":8},{"x":994.88,"y":488.41,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":1006.22,"y":489.32,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":1017.56,"y":490.21,"sector":2,"drsZone":false,"pitLane":false,"corner":0},{"x":1028.9,"y":491.12,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1040.23,"y":492.06,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1051.57,"y":493.03,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1062.89,"y":494.1,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1074.21,"y":495.26,"sector":3,"drsZone":false,"pitLane":false,"corner":7},{"x":1085.51,"y":496.55,"sector":3,"drsZone":false,"pitLane":false,"corner":7},{"x":1096.78,"y":498.04,"sector":3,"drsZone":false,"pitLane":false,"corner":7},{"x":1108.02,"y":499.8,"sector":3,"drsZone":false,"pitLane":false,"corner":7},{"x":1119.19,"y":501.95,"sector":3,"drsZone":false,"pitLane":false,"corner":7},{"x":1130.24,"y":504.62,"sector":3,"drsZone":false,"pitLane":false,"corner":7},{"x":1141.09,"y":508.03,"sector":3,"drsZone":false,"pitLane":false,"corner":7},{"x":1151.64,"y":512.28,"sector":3,"drsZone":false,"pitLane":false,"corner":7},{"x":1161.79,"y":517.4,"sector":3,"drsZone":false,"pitLane":false,"corner":7},{"x":1171.59,"y":523.17,"sector":3,"drsZone":false,"pitLane":false,"corner":7},{"x":1181.1,"y":529.41,"sector":3,"drsZone":false,"pitLane":false,"corner":7},{"x":1190.33,"y":536.05,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1199.45,"y":542.85,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1208.52,"y":549.72,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1217.56,"y":556.62,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1226.58,"y":563.55,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1235.59,"y":570.5,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1244.59,"y":577.46,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1253.57,"y":584.43,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1262.55,"y":591.41,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1271.53,"y":598.4,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1280.5,"y":605.4,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1289.46,"y":612.4,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1298.43,"y":619.4,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1307.39,"y":626.4,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1316.36,"y":633.4,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1325.35,"y":640.38,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1334.33,"y":647.36,"sector":3,"drsZone":false,"pitLane":false,"corner":6},{"x":1342.97,"y":654.75,"sector":3,"drsZone":false,"pitLane":false,"corner":6},{"x":1351.3,"y":662.5,"sector":3,"drsZone":false,"pitLane":false,"corner":6},{"x":1354.77,"y":672.32,"sector":3,"drsZone":false,"pitLane":false,"corner":6},{"x":1347.62,"y":681.06,"sector":3,"drsZone":false,"pitLane":false,"corner":6},{"x":1339.3,"y":688.81,"sector":3,"drsZone":false,"pitLane":false,"corner":6},{"x":1331.2,"y":696.79,"sector":3,"drsZone":false,"pitLane":false,"corner":6},{"x":1323.31,"y":704.99,"sector":3,"drsZone":false,"pitLane":false,"corner":6},{"x":1315.3,"y":713.07,"sector":3,"drsZone":false,"pitLane":false,"corner":6},{"x":1307.2,"y":721.05,"sector":3,"drsZone":false,"pitLane":false,"corner":6},{"x":1299.2,"y":729.14,"sector":3,"drsZone":false,"pitLane":false,"corner":6},{"x":1291.61,"y":737.61,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1285.07,"y":746.91,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1278.95,"y":756.49,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1272.82,"y":766.07,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1266.65,"y":775.63,"sector":3,"drsZone":false,"pitLane":false,"corner":5},{"x":1260.09,"y":784.92,"sector":3,"drsZone":false,"pitLane":false,"corner":5},{"x":1252.13,"y":792.98,"sector":3,"drsZone":false,"pitLane":false,"corner":5},{"x":1242.38,"y":798.79,"sector":3,"drsZone":false,"pitLane":false,"corner":5},{"x":1231.62,"y":802.41,"sector":3,"drsZone":false,"pitLane":false,"corner":5},{"x":1220.33,"y":803.51,"sector":3,"drsZone":false,"pitLane":false,"corner":5},{"x":1209.24,"y":801.22,"sector":3,"drsZone":false,"pitLane":false,"corner":5},{"x":1198.69,"y":797.0,"sector":3,"drsZone":false,"pitLane":false,"corner":5},{"x":1188.28,"y":792.4,"sector":3,"drsZone":false,"pitLane":false,"corner":5},{"x":1177.94,"y":787.66,"sector":3,"drsZone":false,"pitLane":false,"corner":5},{"x":1167.63,"y":782.86,"sector":3,"drsZone":false,"pitLane":false,"corner":5},{"x":1157.34,"y":778.02,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1147.06,"y":773.15,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1136.78,"y":768.27,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1126.48,"y":763.45,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1116.12,"y":758.75,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1105.6,"y":754.42,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1094.58,"y":753.82,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1087.16,"y":762.05,"sector":3,"drsZone":false,"pitLane":false,"corner":4},{"x":1085.23,"y":773.19,"sector":3,"drsZone":false,"pitLane":false,"corner":4},{"x":1084.44,"y":784.54,"sector":3,"drsZone":false,"pitLane":false,"corner":4},{"x":1083.34,"y":795.86,"sector":3,"drsZone":false,"pitLane":false,"corner":4},{"x":1081.96,"y":807.15,"sector":3,"drsZone":false,"pitLane":false,"corner":4},{"x":1079.99,"y":818.35,"sector":3,"drsZone":false,"pitLane":false,"corner":4},{"x":1076.94,"y":829.28,"sector":3,"drsZone":false,"pitLane":false,"corner":4},{"x":1070.62,"y":838.65,"sector":3,"drsZone":false,"pitLane":false,"corner":4},{"x":1061.36,"y":845.15,"sector":3,"drsZone":false,"pitLane":false,"corner":4},{"x":1050.54,"y":848.54,"sector":3,"drsZone":false,"pitLane":false,"corner":4},{"x":1039.22,"y":849.53,"sector":3,"drsZone":false,"pitLane":false,"corner":4},{"x":1027.87,"y":849.02,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":1016.62,"y":847.34,"sector":3,"drsZone":false,"pitLane":false,"corner":3},{"x":1005.39,"y":845.49,"sector":3,"drsZone":false,"pitLane":false,"corner":3},{"x":994.18,"y":843.6,"sector":3,"drsZone":false,"pitLane":false,"corner":3},{"x":982.96,"y":841.68,"sector":3,"drsZone":false,"pitLane":false,"corner":3},{"x":971.75,"y":839.75,"sector":3,"drsZone":false,"pitLane":false,"corner":3},{"x":960.55,"y":837.8,"sector":3,"drsZone":false,"pitLane":false,"corner":3},{"x":949.34,"y":835.84,"sector":3,"drsZone":false,"pitLane":false,"corner":3},{"x":938.14,"y":833.88,"sector":3,"drsZone":false,"pitLane":false,"corner":3},{"x":926.93,"y":831.92,"sector":3,"drsZone":false,"pitLane":false,"corner":3},{"x":915.73,"y":829.94,"sector":3,"drsZone":false,"pitLane":false,"corner":3},{"x":904.53,"y":827.97,"sector":3,"drsZone":false,"pitLane":false,"corner":3},{"x":893.33,"y":825.99,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":882.13,"y":824.01,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":870.93,"y":822.02,"sector":3,"drsZone":false,"pitLane":false,"corner":0},{"x":859.73,"y":820.03,"sector":3,"drsZone":true,"pitLane":false,"corner":0},{"x":848.53,"y":818.04,"sector":3,"drsZone":true,"pitLane":false,"corner":0},{"x":837.33,"y":816.05,"sector":3,"drsZone":true,"pitLane":false,"corner":0},{"x":826.13,"y":814.06,"sector":3,"drsZone":true,"pitLane":false,"corner":0},{"x":814.93,"y":812.07,"sector":3,"drsZone":true,"pitLane":false,"corner":2},{"x":803.73,"y":810.08,"sector":3,"drsZone":true,"pitLane":false,"corner":2},{"x":792.53,"y":808.08,"sector":3,"drsZone":true,"pitLane":false,"corner":2},{"x":781.33,"y":806.08,"sector":3,"drsZone":true,"pitLane":false,"corner":2},{"x":770.13,"y":804.09,"sector":3,"drsZone":true,"pitLane":false,"corner":2},{"x":758.94,"y":802.09,"sector":3,"drsZone":true,"pitLane":false,"corner":2},{"x":747.74,"y":800.09,"sector":3,"drsZone":true,"pitLane":false,"corner":2},{"x":736.54,"y":798.1,"sector":3,"drsZone":true,"pitLane":false,"corner":2},{"x":725.34,"y":796.1,"sector":3,"drsZone":true,"pitLane":false,"corner":2},{"x":714.14,"y":794.1,"sector":3,"drsZone":true,"pitLane":false,"corner":2},{"x":702.94,"y":792.1,"sector":3,"drsZone":true,"pitLane":false,"corner":2},{"x":691.75,"y":790.11,"sector":3,"drsZone":true,"pitLane":false,"corner":0},{"x":680.55,"y":788.11,"sector":3,"drsZone":true,"pitLane":false,"corner":0},{"x":669.35,"y":786.12,"sector":3,"drsZone":true,"pitLane":false,"corner":0},{"x":658.15,"y":784.12,"sector":3,"drsZone":true,"pitLane":false,"corner":0},{"x":646.95,"y":782.13,"sector":3,"drsZone":true,"pitLane":false,"corner":1},{"x":635.75,"y":780.13,"sector":3,"drsZone":true,"pitLane":false,"corner":1},{"x":624.55,"y":778.14,"sector":3,"drsZone":true,"pitLane":true,"corner":1},{"x":613.35,"y":776.15,"sector":3,"drsZone":true,"pitLane":true,"corner":1},{"x":602.15,"y":774.16,"sector":3,"drsZone":true,"pitLane":true,"corner":1},{"x":590.96,"y":772.16,"sector":3,"drsZone":true,"pitLane":true,"corner":1},{"x":579.76,"y":770.16,"sector":3,"drsZone":true,"pitLane":true,"corner":1},{"x":568.56,"y":768.15,"sector":3,"drsZone":true,"pitLane":true,"corner":1},{"x":557.37,"y":766.12,"sector":3,"drsZone":true,"pitLane":true,"corner":1},{"x":546.19,"y":764.04,"sector":3,"drsZone":false,"pitLane":true,"corner":1},{"x":535.03,"y":761.83,"sector":3,"drsZone":false,"pitLane":true,"corner":1}];

// ─── SVG viewBox ───────────────────────────────────────────────────────────
const AUS_VIEWBOX = { w: 1424, h: 983 };

// ─── Albert Park pit lane waypoints (SVG coords) ─────────────────────────────
// Geometry from official SVG: entry after T15 (right, x≈1100), exit before T1 (left, x≈546)
// Lane runs east→west at y≈820, 18px south of the racing line.
// STOP ZONE at mid-lane x≈758 (pit box area).
const AUS_PIT_LANE = [
    {x:1100, y:820},  // 0  — entry (after T15, right side)
    {x:1028, y:821},  // 1
    {x: 961, y:820},  // 2
    {x: 893, y:820},  // 3  — pit box zone start
    {x: 825, y:820},  // 4
    {x: 758, y:820},  // 5  — STOP ZONE (crew works here)
    {x: 692, y:820},  // 6
    {x: 625, y:819},  // 7  — exiting boxes
    {x: 558, y:819},  // 8
    {x: 490, y:819},  // 9
    {x: 420, y:819},  // 10
    {x: 375, y:816},  // 11 — exit road curves north
    {x: 378, y:760},  // 12
    {x: 385, y:695},  // 13
    {x: 390, y:670},  // 14 — rejoins track at T1/T2 (fraction ~0.05)
];

class TrackRenderer {
    constructor(canvasId, config = {}) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) throw new Error(`Canvas "${canvasId}" not found`);
        this.ctx = this.canvas.getContext('2d');

        this.config = {
            padding:    config.padding    || 10,
            carRadius:  config.carRadius  || 8,
            ...config,
        };

        this.trackData       = null;
        this.trackPath       = null;   // screen-space sample points for car positions
        this.svgTransform    = null;   // {scale, offsetX, offsetY}
        this.trackImageCache = null;
        this.isAUS           = false;
        this._svgImage       = null;   // the loaded SVG Image object
        this._svgReady       = false;

        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        const r = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width  = Math.max(r.width,  200);
        this.canvas.height = Math.max(r.height, 150);
        if (this.trackData) this._rebuild();
    }

    // ── Public: load circuit ─────────────────────────────────────────────────
    loadCircuit(circuitData) {
        this.trackData = circuitData;
        this.isAUS     = (circuitData.circuit_id === 'AUS');
        this._rebuild();
    }

    _rebuild() {
        this._computeTransform();
        this._buildTrackPath(this.isAUS ? AUS_TRACK_POINTS : (this.trackData?.coordinates || []));

        if (this.isAUS) {
            this._loadSVGBackground();
        } else {
            this._buildGenericCache();
        }
    }

    // ── Compute scale/offset to fit SVG/coords into canvas ───────────────────
    _computeTransform() {
        const pad = this.config.padding;
        const avW = this.canvas.width  - 2 * pad;
        const avH = this.canvas.height - 2 * pad;

        if (this.isAUS) {
            // Preserve the circuit's actual aspect ratio (width/height)
            const circuitAspect = AUS_VIEWBOX.w / AUS_VIEWBOX.h;  // 1.45
            const canvasAspect = avW / avH;
            
            let scale, offsetX, offsetY;
            
            if (canvasAspect > circuitAspect) {
                // Canvas is wider: constrain by height
                scale = avH / AUS_VIEWBOX.h;
                offsetX = pad + (avW - AUS_VIEWBOX.w * scale) / 2;
                offsetY = pad;
            } else {
                // Canvas is taller: constrain by width
                scale = avW / AUS_VIEWBOX.w;
                offsetX = pad;
                offsetY = pad + (avH - AUS_VIEWBOX.h * scale) / 2;
            }
            
            this.svgTransform = { scale, offsetX, offsetY };
        } else {
            this.svgTransform = null;
        }
    }

    // ── Build screen-space car position path ─────────────────────────────────
    _buildTrackPath(coords) {
        if (!coords || !coords.length) { this.trackPath = []; return; }

        if (this.isAUS && this.svgTransform) {
            const { scale, offsetX, offsetY } = this.svgTransform;
            this.trackPath = coords.map(pt => ({
                x:       pt.x * scale + offsetX,
                y:       pt.y * scale + offsetY,
                sector:  pt.sector  || 1,
                drsZone: pt.drsZone || false,
                corner:  pt.corner  || 0,
            }));
            return;
        }

        // Generic: auto-scale with Y-flip for GPS coords
        let minX=Infinity, minY=Infinity, maxX=-Infinity, maxY=-Infinity;
        coords.forEach(pt => {
            if(pt.x<minX)minX=pt.x; if(pt.y<minY)minY=pt.y;
            if(pt.x>maxX)maxX=pt.x; if(pt.y>maxY)maxY=pt.y;
        });
        const pad=this.config.padding, avW=this.canvas.width-2*pad, avH=this.canvas.height-2*pad;
        const scale=Math.min(avW/(maxX-minX||1), avH/(maxY-minY||1));
        const offX=pad+(avW-(maxX-minX)*scale)/2, offY=pad+(avH-(maxY-minY)*scale)/2;
        this.trackPath = coords.map(pt=>({
            x: (pt.x-minX)*scale+offX,
            y: (maxY-pt.y)*scale+offY,
            sector:  pt.sector||1,
            drsZone: pt.drsZone||false,
            corner:  pt.corner||0,
        }));
    }

    // ── AUS: load the official SVG as a background image ─────────────────────
    _loadSVGBackground() {
        if (this._svgImage && this._svgReady) {
            // Already loaded — just rebuild cache
            this._buildAUSCache();
            return;
        }

        const img = new Image();
        this._svgImage = img;
        this._svgReady = false;

        img.onload = () => {
            this._svgReady = true;
            this._buildAUSCache();
        };
        img.onerror = () => {
            console.error('[TrackRenderer] Failed to load SVG background');
            // Fallback: draw a simple placeholder
            this._buildFallbackCache();
        };

        // Load from the frontend folder (served by FastAPI)
        img.src = '/Albert_Park_Circuit_2021.svg';
    }

    // ── Build AUS cache: SVG image + circuit name label ───────────────────────
    _buildAUSCache() {
        const c = document.createElement('canvas');
        c.width  = this.canvas.width;
        c.height = this.canvas.height;
        const ctx = c.getContext('2d');

        // Dark background matching the canvas container
        ctx.fillStyle = '#0a0a0a';
        ctx.fillRect(0, 0, c.width, c.height);

        if (this._svgReady && this._svgImage && this.svgTransform) {
            const { scale, offsetX, offsetY } = this.svgTransform;
            const dw = AUS_VIEWBOX.w * scale;
            const dh = AUS_VIEWBOX.h * scale;
            ctx.drawImage(this._svgImage, offsetX, offsetY, dw, dh);
        }

        this._drawCircuitLabel(ctx);
        this.trackImageCache = c;

        // Trigger a redraw of the live canvas
        this.drawTrack();
    }

    _buildFallbackCache() {
        const c = document.createElement('canvas');
        c.width = this.canvas.width; c.height = this.canvas.height;
        const ctx = c.getContext('2d');
        ctx.fillStyle = '#0a0a0a';
        ctx.fillRect(0, 0, c.width, c.height);
        ctx.fillStyle = '#333';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Albert Park Circuit', c.width/2, c.height/2);
        this.trackImageCache = c;
        this.drawTrack();
    }

    // ── Generic polyline circuit cache ────────────────────────────────────────
    _buildGenericCache() {
        if (!this.trackPath || !this.trackPath.length) return;
        const c = document.createElement('canvas');
        c.width = this.canvas.width; c.height = this.canvas.height;
        const ctx = c.getContext('2d');

        ctx.fillStyle = '#0a0a0a';
        ctx.fillRect(0, 0, c.width, c.height);

        // White border
        ctx.strokeStyle = '#FFFFFF';
        ctx.lineWidth   = 16;
        ctx.lineCap     = 'round'; ctx.lineJoin = 'round';
        ctx.beginPath();
        this.trackPath.forEach((pt,i) => i===0 ? ctx.moveTo(pt.x,pt.y) : ctx.lineTo(pt.x,pt.y));
        ctx.closePath(); ctx.stroke();

        // Dark surface
        ctx.strokeStyle = '#111118'; ctx.lineWidth = 12;
        ctx.beginPath();
        this.trackPath.forEach((pt,i) => i===0 ? ctx.moveTo(pt.x,pt.y) : ctx.lineTo(pt.x,pt.y));
        ctx.closePath(); ctx.stroke();

        // Sector colour lines
        const SECTOR_COLORS = {1:'#E91E8C', 2:'#FFD700', 3:'#1E90FF'};
        let i=0, n=this.trackPath.length;
        while(i<n) {
            const sec=this.trackPath[i].sector, col=SECTOR_COLORS[sec]||'#fff';
            const start=i;
            while(i<n && this.trackPath[i].sector===sec) i++;
            const seg=this.trackPath.slice(start, i+1);
            ctx.strokeStyle=col; ctx.lineWidth=6;
            ctx.shadowColor=col; ctx.shadowBlur=6;
            ctx.beginPath();
            seg.forEach((pt,j)=>j===0?ctx.moveTo(pt.x,pt.y):ctx.lineTo(pt.x,pt.y));
            ctx.stroke(); ctx.shadowBlur=0;
        }

        this._drawCircuitLabel(ctx);
        this.trackImageCache = c;
    }

    // ── Circuit name label (top-left) ─────────────────────────────────────────
    _drawCircuitLabel(ctx) {
        if (!this.trackData?.name) return;
        ctx.save();
        ctx.fillStyle   = 'rgba(0,0,0,0.85)';
        ctx.strokeStyle = '#00FF9D';
        ctx.lineWidth   = 1.5;
        ctx.fillRect(12, 12, 210, 28);
        ctx.strokeRect(12, 12, 210, 28);
        ctx.fillStyle    = '#FFFFFF';
        ctx.font         = 'bold 12px Arial';
        ctx.textAlign    = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.trackData.name, 22, 26);
        ctx.restore();
    }

    // ── Draw cached track to live canvas ─────────────────────────────────────
    drawTrack() {
        if (this.trackImageCache) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.drawImage(this.trackImageCache, 0, 0);
        }
    }

    // ── Get canvas x,y from lap progress 0→1 ─────────────────────────────────
    getPositionOnTrack(progress) {
        if (!this.trackPath || !this.trackPath.length) return null;
        const n   = this.trackPath.length;
        const idx = Math.floor(progress * n) % n;
        const nxt = (idx + 1) % n;
        const frac= (progress * n) % 1;
        return {
            x: this.trackPath[idx].x + (this.trackPath[nxt].x - this.trackPath[idx].x) * frac,
            y: this.trackPath[idx].y + (this.trackPath[nxt].y - this.trackPath[idx].y) * frac,
        };
    }

    // ── Get canvas x,y along pit lane (progress 0→1) ──────────────────────────
    getPitLanePosition(progress) {
        if (!this.svgTransform) return null;
        const pts = AUS_PIT_LANE;
        const n   = pts.length - 1;
        const clamped = Math.max(0, Math.min(1, progress));
        const idx  = Math.min(Math.floor(clamped * n), n - 1);
        const nxt  = Math.min(idx + 1, n);
        const frac = (clamped * n) - idx;
        const { scale, offsetX, offsetY } = this.svgTransform;
        const x = (pts[idx].x + (pts[nxt].x - pts[idx].x) * frac) * scale + offsetX;
        const y = (pts[idx].y + (pts[nxt].y - pts[idx].y) * frac) * scale + offsetY;
        return { x, y };
    }

    // ── Render a single car marker ────────────────────────────────────────────
    renderCar(x, y, carData) {
        const r   = this.config.carRadius;
        const ctx = this.ctx;
        const inPit = carData.inPit || false;
        ctx.save();

        // Pit lane cars: orange theme
        const dotColor = inPit ? '#FF8C00'
                       : (carData.teamColor || '#888');
        const borderColor = inPit ? '#FFD700' : '#FFFFFF';

        if (!inPit && carData.position === 1) { ctx.shadowColor = carData.teamColor; ctx.shadowBlur = 20; }
        if (!inPit && carData.drsActive)      { ctx.shadowColor = '#00FF00';         ctx.shadowBlur = 14; }

        // Leader glow ring
        if (!inPit && carData.position === 1) {
            ctx.fillStyle = carData.teamColor;
            ctx.beginPath(); ctx.arc(x, y, r+3, 0, Math.PI*2); ctx.fill();
        }

        // Car dot
        ctx.fillStyle   = dotColor;
        ctx.strokeStyle = borderColor;
        ctx.lineWidth   = inPit ? 2.5 : 2;
        ctx.shadowBlur  = 0;
        ctx.globalAlpha = inPit ? 0.85 : 1.0;
        ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI*2); ctx.fill(); ctx.stroke();
        ctx.globalAlpha = 1.0;

        // Tag above dot
        const tagW=30, tagH=14, tagY=y-r-16;
        ctx.fillStyle   = inPit ? 'rgba(30,15,0,0.95)' : 'rgba(0,0,0,0.92)';
        ctx.strokeStyle = dotColor;
        ctx.lineWidth   = 1.5;
        ctx.fillRect(x-tagW/2, tagY-tagH/2, tagW, tagH);
        ctx.strokeRect(x-tagW/2, tagY-tagH/2, tagW, tagH);
        ctx.fillStyle    = inPit ? '#FFD700' : '#FFF';
        ctx.font         = 'bold 8px Arial';
        ctx.textAlign    = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(carData.driverAbbr || '?', x, tagY);

        // Badge below dot: PIT or position number
        if (inPit) {
            // PIT text badge
            ctx.fillStyle = '#FF8C00';
            const bw = 24, bh = 12;
            ctx.fillRect(x-bw/2, y+r+3, bw, bh);
            ctx.fillStyle = '#000';
            ctx.font = 'bold 7px Arial'; ctx.textBaseline = 'middle';
            ctx.fillText('PIT', x, y+r+3+bh/2);
        } else {
            const badgeCol = carData.position===1 ? '#FFD700' : '#00FF9D';
            ctx.fillStyle = badgeCol;
            ctx.beginPath(); ctx.arc(x, y+r+7, 7, 0, Math.PI*2); ctx.fill();
            ctx.fillStyle = '#000'; ctx.font = 'bold 7px Arial'; ctx.textBaseline = 'middle';
            ctx.fillText(carData.position, x, y+r+8);
        }

        ctx.restore();
    }

    clear() { this.ctx.clearRect(0,0,this.canvas.width,this.canvas.height); }
    destroy() { window.removeEventListener('resize', ()=>this.resize()); }
}

if (typeof module !== 'undefined' && module.exports) module.exports = TrackRenderer;
