# VTK Installation Guide

Builds VTK 9.6.2 from source on Ubuntu for `vtk/SimpleRayCast`. The Python code only needs `pip install vtk`.

## 1. Install the packages

```bash
sudo apt update
sudo apt install build-essential cmake mesa-common-dev mesa-utils freeglut3-dev ninja-build
```

## 2. Get the source

```bash
mkdir -p ~/vtk && cd ~/vtk
wget https://www.vtk.org/files/release/9.6/VTK-9.6.2.tar.gz
echo "aed12cec12a9609179bf66329070266627ca64244a10856a452b2a17ffb04a1d  VTK-9.6.2.tar.gz" | sha256sum -c
tar xzf VTK-9.6.2.tar.gz
mv VTK-9.6.2 source
```

## 3. Configure and build

```bash
cmake -GNinja -S ~/vtk/source -B ~/vtk/build -DCMAKE_BUILD_TYPE=Release
cmake --build ~/vtk/build
```

This takes from about 30 minutes to several hours.

## 4. Verify

Build `SimpleRayCast` using step 3 of the [README](../README.md#usage).

## Troubleshooting

| Problem | Fix |
| --- | --- |
| CMake can't find OpenGL | Install `mesa-common-dev` and `freeglut3-dev`, delete `~/vtk/build`, configure again |
| Build is killed or freezes | Out of memory: run the build command again with `-j 2`. It resumes where it stopped. |
| No window opens over SSH | Run locally or use `ssh -X` |
