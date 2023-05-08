from flask import Flask, request, jsonify
from intersection import *

# Get all the matrixes in a list
total = []
for row in all_streets.itertuples():
    total.append(row[1])

def positionsToJson(index):
    json_dict = []
    matrix = total[index]
    # print(matrix)
    for y in range(len(matrix)):
        for x in range(len(matrix)):
            value = matrix[y][x]
            if value[0] != 0:
                pos = {
                    "id": int(value[1]),
                    "type": int(value[0]),
                    "x": float(x),
                    "y": 0.0,
                    "z": float(-y)
                }
                json_dict.append(pos)
    return jsonify({'agents': json_dict})


car_agents = []
for i in range(5, 5+NUM_CARS): # First four are the stoplights
    pos = {
        "id": i,
        "type": 4,
        "x": 0.0,
        "y": 0.0,
        "z": 0.0
    }
    car_agents.append(pos)

index_count = 0

app = Flask("Test")

@app.route('/', methods=['GET'])
def agents_position():
    if request.method == 'GET':
        global index_count
        if index_count < len(total):
            positions = positionsToJson(index_count)
            index_count += 1
            return positions
        print("End of simultaion")
        return jsonify({"agents": {}})

@app.route('/init', methods=['GET'])
def agents_init():
    if request.method == 'GET':
        global index_count
        index_count = 0
        return jsonify({"agents": car_agents})

if __name__=='__main__':
    app.run(host="localhost", port=8585, debug=True)