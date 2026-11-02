"""Export a VTK volume + transfer function + view file to a COLMAP-style dataset.

Produces (in <out>/sparse/0/):
    points3D.ply   point cloud of voxels made visible by the opacity TF, colored by the color TF
    points3D.bin   same points in COLMAP binary format
    cameras.bin    one PINHOLE camera matching the VTK camera (view angle, window size)
    images.bin     one pose per view in the views .bin (image j -> "<j+1>.png", as SimpleRayCast saves them)

and (in <out>/images/, if RENDER) <j+1>.png rendered from each view with the same settings as SimpleRayCast.

Usage: edit the settings below, then run
    python export_colmap.py
"""
import os
import struct

import numpy as np
import vtk
from tqdm import tqdm
from vtk.util import numpy_support

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
DATA = os.path.join(BASE, "data")

VOLUME = os.path.join(DATA, "chameleon_256x256x256_normalized_space-1.vtk")  # .vtk structured points file
VIEWS = os.path.join(DATA, "trainviews_1_1201_1_1.bin")  # views .bin written by the view-generation notebook
TF = "chameleon"  # key of TRANSFER_FUNCTIONS
OUT = os.path.join(BASE, "data", "chameleon_colmap")  # output directory for COLMAP-style dataset
WIDTH = 256  # must match renWin->SetSize() of the renders
HEIGHT = 256
MIN_OPACITY = 0.0005  # drop voxels with TF opacity at or below this
VIEW_ANGLE = 30.0  # must match SetViewAngle()

RENDER = True  # also ray cast every view into <OUT>/images/
SAMPLE_DISTANCE = 0.1  # volumeMapper->SetSampleDistance() in SimpleRayCast
CLIPPING_RANGE = (0.1, 1000)  # SetClippingRange() in SimpleRayCast

# Same control points as the OTF_* / CTF_* macros in vtk/SimpleRayCast.cxx
# OTF: (scalar, opacity)   CTF: (scalar, r, g, b)
TRANSFER_FUNCTIONS = {
    "chameleon": {
        "otf": [(0.0, 0.0), (0.134375, 0.0), (0.175, 0.268018), (0.23125, 0.0), (0.40625, 0.0), (1.0, 1.0)],
        "ctf": [(0.0, 0.02, 0.3813, 0.9981), (0.142857, 0.02, 0.6188, 0.796), (0.238095, 0.02, 0.757035, 0.603735),
                (0.404762, 0.493355, 0.961904, 0.111195), (0.5, 0.999529, 0.999519, 0.0134885),
                (0.952381, 0.798903, 0.0433335, 0.358434), (1.0, 0.6837, 0.05, 0.4139)],
    }
}


def make_tf(tf):
    """vtkColorTransferFunction (RGB space) carrying the opacity TF, so one MapScalars call gives RGBA."""
    otf = vtk.vtkPiecewiseFunction()
    
    for x, a in tf["otf"]:
        otf.AddPoint(x, a)

    ctf = vtk.vtkDiscretizableColorTransferFunction()
    
    for x, r, g, b in tf["ctf"]:
        ctf.AddRGBPoint(x, r, g, b)

    ctf.SetScalarOpacityFunction(otf)
    ctf.EnableOpacityMappingOn()
    
    return ctf


def read_views(path):
    """Same parsing as getSizes()/main() in SimpleRayCast.cxx: name_<block>_<ray>_<sample>_<up>.bin, 9 doubles each."""
    sizes = [int(s) for s in os.path.splitext(os.path.basename(path))[0].split("_")[1:5]]
    
    return np.fromfile(path, dtype=np.float64).reshape(int(np.prod(sizes)), 9)


def read_volume(path):
    reader = vtk.vtkStructuredPointsReader()
    reader.SetFileName(path)
    reader.Update()
    return reader.GetOutput()


def volume_to_points(volume, tf, min_opacity):
    """Point cloud (vtkPolyData with RGBA point scalars) of the voxels whose TF opacity passes min_opacity."""
    colors = vtk.vtkImageMapToColors()
    colors.SetInputData(volume)
    colors.SetLookupTable(make_tf(tf))
    colors.SetOutputFormatToRGBA()

    # Opacity is the 8-bit alpha channel
    threshold = vtk.vtkThresholdPoints()
    threshold.SetInputConnection(colors.GetOutputPort())
    threshold.SetInputArrayComponent(3)
    threshold.SetUpperThreshold(min_opacity * 255)  # THRESHOLD_UPPER keeps alpha >= UpperThreshold
    threshold.SetThresholdFunction(vtk.vtkThresholdPoints.THRESHOLD_UPPER)
    threshold.Update()

    return threshold.GetOutput()


def make_renderer(volume_data, tf, width, height):
    """Same pipeline as main() in SimpleRayCast.cxx, rendered off screen."""
    vtk.vtkMultiThreader.SetGlobalMaximumNumberOfThreads(1)

    otf = vtk.vtkPiecewiseFunction()
    for x, a in tf["otf"]:
        otf.AddPoint(x, a)

    ctf = vtk.vtkColorTransferFunction()
    for x, r, g, b in tf["ctf"]:
        ctf.AddRGBPoint(x, r, g, b)

    prop = vtk.vtkVolumeProperty()
    prop.SetColor(ctf)
    prop.SetScalarOpacity(otf)
    prop.SetInterpolationTypeToLinear()

    mapper = vtk.vtkFixedPointVolumeRayCastMapper()
    mapper.SetInputData(volume_data)
    mapper.SetSampleDistance(SAMPLE_DISTANCE)
    mapper.SetBlendModeToComposite()

    volume = vtk.vtkVolume()
    volume.SetMapper(mapper)
    volume.SetProperty(prop)

    ren = vtk.vtkRenderer()
    ren.AddVolume(volume)
    ren.SetBackground(0, 0, 0)

    ren_win = vtk.vtkRenderWindow()
    ren_win.SetOffScreenRendering(1)
    ren_win.AddRenderer(ren)
    ren_win.SetSize(width, height)

    camera = ren.GetActiveCamera()
    camera.SetViewAngle(VIEW_ANGLE)
    camera.SetClippingRange(*CLIPPING_RANGE)

    return ren_win, camera


def render_images(out_dir, volume_data, tf, views, width, height):
    """Mirrors vtkTimerCallback2::Execute(): set the view, grab the RGB back buffer, save "<j+1>.png"."""
    os.makedirs(out_dir, exist_ok=True)
    ren_win, camera = make_renderer(volume_data, tf, width, height)

    for j, v in enumerate(tqdm(views, desc="Rendering", unit="view")):
        camera.SetPosition(*v[0:3])
        camera.SetFocalPoint(*v[3:6])
        camera.SetViewUp(*v[6:9])
        ren_win.Render()

        grab = vtk.vtkWindowToImageFilter()
        grab.SetInput(ren_win)
        grab.SetScale(1)
        grab.SetInputBufferTypeToRGB()
        grab.ReadFrontBufferOff()

        writer = vtk.vtkPNGWriter()
        writer.SetFileName(os.path.join(out_dir, f"{j + 1}.png"))
        writer.SetInputConnection(grab.GetOutputPort())
        writer.Write()


def write_ply(path, points):
    # Same layout as storePly() in 3D Gaussian Splatting (x y z nx ny nz red green blue)
    normals = vtk.vtkFloatArray()
    normals.SetNumberOfComponents(3)
    normals.SetNumberOfTuples(points.GetNumberOfPoints())
    normals.Fill(0.0)
    points.GetPointData().SetNormals(normals)

    writer = vtk.vtkPLYWriter()
    writer.SetFileName(path)
    writer.SetInputData(points)
    writer.SetFileTypeToBinary()
    writer.SetDataByteOrderToLittleEndian()
    writer.SetArrayName(points.GetPointData().GetScalars().GetName())
    writer.Write()


def write_points3d_bin(path, xyz, rgb):
    with open(path, "wb") as f:
        f.write(struct.pack("<Q", len(xyz)))
        for idx, (p, c) in enumerate(zip(xyz, rgb), start=1):
            # id, xyz, rgb, error, track_length (no 2D observations)
            f.write(struct.pack("<Q3d3BdQ", idx, *p, *c, 0.0, 0))


def vtk_camera_to_colmap(position, focal, up):
    """World-to-camera R, t in COLMAP/OpenCV convention (x right, y down, z forward)."""
    camera = vtk.vtkCamera()
    camera.SetPosition(position)
    camera.SetFocalPoint(focal)
    camera.SetViewUp(up)
    view = camera.GetViewTransformMatrix()
    # VTK view space is OpenGL (y up, looking down -z): flip y and z
    m = np.array([[view.GetElement(r, c) for c in range(4)] for r in range(4)])
    m[1:3] *= -1

    return m[:3, :3], m[:3, 3]


def rotmat_to_qvec(R):
    q = [0.0] * 4
    vtk.vtkMath.Matrix3x3ToQuaternion(R.tolist(), q)  # (w, x, y, z)
    return q if q[0] >= 0 else [-c for c in q]


def write_cameras_bin(path, width, height, view_angle_deg):
    # vtkCamera::ViewAngle is the vertical field of view
    f = (height / 2) / np.tan(np.radians(view_angle_deg) / 2)
    
    with open(path, "wb") as fp:
        fp.write(struct.pack("<Q", 1))
        fp.write(struct.pack("<iiQQ4d", 1, 1, width, height, f, f, width / 2, height / 2))  # model 1 = PINHOLE


def write_images_bin(path, views):
    with open(path, "wb") as f:
        f.write(struct.pack("<Q", len(views)))
        for j, v in enumerate(views):
            R, t = vtk_camera_to_colmap(v[0:3].copy(), v[3:6].copy(), v[6:9].copy())
            f.write(struct.pack("<i4d3di", j + 1, *rotmat_to_qvec(R), *t, 1))
            f.write(f"{j + 1}.png".encode() + b"\x00")
            f.write(struct.pack("<Q", 0))  # no 2D points


def main():
    sparse = os.path.join(OUT, "sparse", "0")
    os.makedirs(sparse, exist_ok=True)

    print(f"Reading {VOLUME} ...")
    volume = read_volume(VOLUME)
    print(f"  dimensions {volume.GetDimensions()}, range {volume.GetScalarRange()}, "
          f"origin {volume.GetOrigin()}, spacing {volume.GetSpacing()}")

    points = volume_to_points(volume, TRANSFER_FUNCTIONS[TF], MIN_OPACITY)
    print(f"  {points.GetNumberOfPoints()} points with TF '{TF}'")
    write_ply(os.path.join(sparse, "points3D.ply"), points)

    xyz = numpy_support.vtk_to_numpy(points.GetPoints().GetData())
    rgb = numpy_support.vtk_to_numpy(points.GetPointData().GetScalars())[:, :3]
    write_points3d_bin(os.path.join(sparse, "points3D.bin"), xyz, rgb)

    views = read_views(VIEWS)
    print(f"  {len(views)} views from {VIEWS}")
    write_cameras_bin(os.path.join(sparse, "cameras.bin"), WIDTH, HEIGHT, VIEW_ANGLE)
    write_images_bin(os.path.join(sparse, "images.bin"), views)

    render_images(os.path.join(OUT, "images"), volume, TRANSFER_FUNCTIONS[TF], views, WIDTH, HEIGHT)

    print(f"Done -> {OUT}")


if __name__ == "__main__":
    main()
