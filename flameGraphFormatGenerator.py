import pandas as pd
import csv
import argparse
import os
import subprocess

flamegraphPlPath = "C:\\dev\\FlameGraph\\flamegraph.pl"

parser = argparse.ArgumentParser(description="A simple script to generate a file that can be used to create flamegraph")
parser.add_argument("input_file_name", type=str, help="Provide the name of the input file")
parser.add_argument('-o', "--output", type=str, help="Name of the output txt file")
parser.add_argument('-s', "--svg", type=str, help="Generate flamegraph vector image")

args = parser.parse_args()

input_file = args.input_file_name
output_csv_file = 'profile.csv'

with open(input_file, 'r', newline='') as infile, open(output_csv_file, 'w', newline='') as outfile:
    csv_writer = csv.writer(outfile, delimiter=',')
    firstLine = "VI Name	VI Time	Sub VIs Time	Total Time	# Runs	Average	Shortest	Longest	Diagram	Display	Draw	Tracking	Locals	Avg Bytes	Min Bytes	Max Bytes	Avg Blocks	Min Blocks	Max Blocks	Project Library	Application Instance"
    data = firstLine.strip().split('\t')
    csv_writer.writerow(data)
    for line in infile:
        data = line.strip().split('\t')
        csv_writer.writerow(data)

data = pd.read_csv('./profile.csv')

viNameList = data['VI Name']
totalViTimeList = data['Total Time']
totalViCnt = len(data['VI Name'])

graph = {}
totalParentTimeMap = {}
totalParentChildTimeMap = {}
vis = {}

i = 0
while i < totalViCnt:
    parentName = viNameList[i].split(':')[-1]
    totalParentTime = totalViTimeList[i]
    totalParentTimeMap[parentName] = totalParentTime
    vis[parentName] = False
    i += 1
    child = []
    while i < totalViCnt and viNameList[i].startswith('-->'):
        childName = viNameList[i].split('-->')[-1].split(':')[-1]
        vis[childName] = False
        totalChildTime = totalViTimeList[i]
        if parentName not in totalParentChildTimeMap.keys():
            totalParentChildTimeMap[parentName] = {}
        totalParentChildTimeMap[parentName][childName] = totalChildTime
        child.append(childName)
        i += 1
    graph[parentName] = child

i = 0
while i < totalViCnt:
    parentName = viNameList[i].split(':')[-1]
    i += 1
    while i < totalViCnt and viNameList[i].startswith('-->'):
        childName = viNameList[i].split('-->')[-1].split(':')[-1]
        totalChildTime = totalViTimeList[i]
        if childName not in totalParentTimeMap.keys():
            totalParentTimeMap[childName] = totalChildTime
        i += 1

def dfs(node:str, graph:map, vis:map, path:str, vec:list, totalParentTimeMap:map, totalParentChildTimeMap:map):
    vis[node] = True

    if node not in graph.keys():
        vec.append(path+';'+node+' '+str(totalParentTimeMap[node]))
        return
    
    for child in graph[node]:
        if vis[child] == False and totalParentChildTimeMap[node][child] == totalParentTimeMap[child]:
            dfs(child, graph, vis, path+';'+node, vec, totalParentTimeMap, totalParentChildTimeMap)
        else:
            vec.append(path+';'+node+';'+child+' '+str(totalParentChildTimeMap[node][child]))
    vis[node] = False

vec = []
dfs('Main.vi',graph , vis, "", vec, totalParentTimeMap, totalParentChildTimeMap)

output_file = 'a.txt'
if args.output is not None:
    output_file = args.output

with open(output_file, "w") as f:
    for line in vec:
        f.write(line[1:])
        f.write('\n')

os.remove(output_csv_file)

if args.svg is not None:
    if not os.path.exists(flamegraphPlPath):
        print("Please provide correct flamegraph.pl path")
    else:
        subprocess.run([
            flamegraphPlPath, 
            "--title", "gRPC Time Analysis", 
            "--countname", "millisecond(s)", 
            "--nametype", "VI:",
            output_file, ">", args.svg
        ], shell=True)