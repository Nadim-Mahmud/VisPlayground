# VisPlayground

Renders a scientific volume from known camera positions with VTK, then exports the images and poses as a COLMAP-style dataset. The example uses the Chameleon CT scan.


## Requirements

- VTK 9 for C++ ([installation guide](docs/vtk-installation.md))
- CMake 3.12+, a C++ compiler and a display
- Python 3 with `numpy`, `vtk`, `tqdm`, `matplotlib` and Jupyter



## Usage

1. Run `notebook/create_Chameleon_data.ipynb`.
2. Run the view generation notebook. It writes `trainviews_1_1201_1_1.bin` and `testviews_1_120_1_1.bin`.
3. Build and run the renderer. Run it from `vtk/`, because images go to `screenShot/` there. Each run overwrites the previous images.

   ```bash
   cd vtk
   cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DVTK_DIR=$HOME/vtk/build/lib/cmake/vtk-9.6
   cmake --build build
   mkdir -p screenShot
   ./build/SimpleRayCast ../notebook/chameleon_256x256x256_normalized_space-1.vtk \
       ../notebook/testviews_1_120_1_1.bin
   ```

4. Export the dataset to `dataset/`:

   ```bash
   cd notebook
   python export_colmap.py chameleon_256x256x256_normalized_space-1.vtk testviews_1_120_1_1.bin \
       --tf chameleon --out ../dataset --images ../vtk/screenShot
   ```

