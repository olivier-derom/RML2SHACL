import subprocess
import psutil
import time
import matplotlib.pyplot as plt
import numpy as np


# different amounts of prefixes
self1 = ["python", "mainold.py", "evaluation/astrea_test/self2/mapping.ttl"]
self2 = ["python", "mainold.py", "evaluation/astrea_test/self2/mapping2.ttl"]
self3 = ["python", "mainold.py", "evaluation/astrea_test/self2/mapping3.ttl"]
self4 = ["python", "mainold.py", "evaluation/astrea_test/self2/mapping4.ttl"]

self6 = ["python", "main.py", "evaluation/astrea_test/self2/mapping.ttl"]
self7 = ["python", "main.py", "evaluation/astrea_test/self2/mapping2.ttl"]
self8 = ["python", "main.py", "evaluation/astrea_test/self2/mapping3.ttl"]
self9 = ["python", "main.py", "evaluation/astrea_test/self2/mapping4.ttl"]

old = [self1, self2, self3, self4]
new = [self6, self7, self8, self9]

sizes = ["17 prefixes", "13 prefixes", "10 prefixes", "6 prefixes"]

timelist = []
for itemindex, item in enumerate(old):
    print(itemindex)
    memory = []
    p = subprocess.Popen(item, shell=True)
    current_process = psutil.Process(p.pid)
    children = psutil.Process(p.pid).children(recursive=True)
    start = time.time()
    while p.poll() is None:
        try:
            currentmem = current_process.memory_info()[0]
            for child in current_process.children(recursive=True):
                currentmem += child.memory_info()[0]
            currentmem = (currentmem / 1024 ** 2)
            memory.append(currentmem)
            continue

        except:
            pass

    ptime = round(time.time() - start, 1)
    x = np.linspace(0, ptime, len(memory))

    # Memory usage
    plt.figure(1)
    plt.plot(x, memory, label=sizes[itemindex])
    plt.legend()
    plt.xlabel('time [s]')
    plt.ylabel('Memory Usage [MiB]')

    # time
    print('----------------------------------')
    print(f"Total execution time in seconds: {ptime}s")
    timelist.append(ptime)


for itemindex, item in enumerate(new):
    memory = []
    p = subprocess.Popen(item, shell=True)
    current_process = psutil.Process(p.pid)
    children = psutil.Process(p.pid).children(recursive=True)
    start = time.time()
    while p.poll() is None:
        try:
            currentmem = current_process.memory_info()[0]
            for child in current_process.children(recursive=True):
                currentmem += child.memory_info()[0]
            currentmem = (currentmem / 1024 ** 2)
            memory.append(currentmem)
            continue

        except:
            pass

    ptime = round(time.time() - start, 1)
    x = np.linspace(0, ptime, len(memory))

    # Memory usage
    plt.figure(2)

    plt.plot(x, memory, label=sizes[itemindex])
    plt.legend()
    plt.xlabel('time [s]')
    plt.ylabel('Memory Usage [MiB]')

    print('----------------------------------')
    print(f"Total execution time in seconds: {ptime}s")
    timelist.append(ptime)


# different file sizes
self1 = ["python", "mainold.py", "evaluation/astrea_test/self/mapping.ttl"]
self2 = ["python", "mainold.py", "evaluation/astrea_test/self/mapping3.ttl"]
self3 = ["python", "mainold.py", "evaluation/astrea_test/self/mapping4.ttl"]
self4 = ["python", "mainold.py", "evaluation/astrea_test/self/mapping5.ttl"]

self6 = ["python", "main.py", "evaluation/astrea_test/self/mapping.ttl"]
self7 = ["python", "main.py", "evaluation/astrea_test/self/mapping3.ttl"]
self8 = ["python", "main.py", "evaluation/astrea_test/self/mapping4.ttl"]
self9 = ["python", "main.py", "evaluation/astrea_test/self/mapping5.ttl"]

old = [self1, self2, self3, self4]
new = [self6, self7, self8, self9]

sizes2 = ["76KB", "50KB", "34KB", "11KB"]

timelist2 = []
for itemindex, item in enumerate(old):
    print(itemindex)
    memory = []
    p = subprocess.Popen(item, shell=True)
    current_process = psutil.Process(p.pid)
    children = psutil.Process(p.pid).children(recursive=True)
    start = time.time()
    while p.poll() is None:
        try:
            currentmem = current_process.memory_info()[0]
            for child in current_process.children(recursive=True):
                currentmem += child.memory_info()[0]
            currentmem = (currentmem / 1024 ** 2)
            memory.append(currentmem)
            continue

        except:
            pass

    ptime = round(time.time() - start, 1)
    x = np.linspace(0, ptime, len(memory))

    # Memory usage
    plt.figure(3)
    plt.plot(x, memory, label=sizes[itemindex])
    plt.legend()
    plt.xlabel('time [s]')
    plt.ylabel('Memory Usage [MiB]')

    # time
    print('----------------------------------')
    print(f"Total execution time in seconds: {ptime}s")
    timelist2.append(ptime)


for itemindex, item in enumerate(new):
    memory = []
    p = subprocess.Popen(item, shell=True)
    current_process = psutil.Process(p.pid)
    children = psutil.Process(p.pid).children(recursive=True)
    start = time.time()
    while p.poll() is None:
        try:
            currentmem = current_process.memory_info()[0]
            for child in current_process.children(recursive=True):
                currentmem += child.memory_info()[0]
            currentmem = (currentmem / 1024 ** 2)
            memory.append(currentmem)
            continue

        except:
            pass

    ptime = round(time.time() - start, 1)
    x = np.linspace(0, ptime, len(memory))

    # Memory usage
    plt.figure(4)

    plt.plot(x, memory, label=sizes[itemindex])
    plt.legend()
    plt.xlabel('time [s]')
    plt.ylabel('Memory Usage [MiB]')

    print('----------------------------------')
    print(f"Total execution time in seconds: {ptime}s")
    timelist2.append(ptime)


for i in range(0, len(timelist)):
    if i < 4:
        ver = 'old'
    else:
        ver = 'new'
    print(ver, sizes[i % 4], ':', timelist[i], 's')

for i in range(0, len(timelist)):
    if i < 4:
        ver = 'old'
    else:
        ver = 'new'
    print(ver, sizes2[i % 4], ':', timelist2[i], 's')

plt.show()
