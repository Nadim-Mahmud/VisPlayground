"""Interactive viewer for a PLY point cloud (e.g. points3D.ply written by export_colmap.py).

Controls (VTK trackball camera):
    left drag   rotate          middle drag / shift+left   pan
    wheel       zoom            r                          reset camera
    + / -       point size      q / e                      quit

Usage:
    python ply3ddrawer.py [path/to/cloud.ply] [--point-size N]
"""
import argparse
import os

import vtk

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
DEFAULT_PLY = os.path.join(BASE, "data", "chameleon_colmap", "sparse", "0", "points3D.ply")


def load_points(path):
    reader = vtk.vtkPLYReader()
    reader.SetFileName(path)
    reader.Update()
    poly = reader.GetOutput()
    # PLY files with "element face 0" give no cells; add one vertex per point so they render
    verts = vtk.vtkVertexGlyphFilter()
    verts.SetInputData(poly)
    verts.Update()
    return verts.GetOutput()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ply", nargs="?", default=DEFAULT_PLY, help="PLY file to view")
    parser.add_argument("--point-size", type=float, default=2.0)
    args = parser.parse_args()

    cloud = load_points(args.ply)
    n = cloud.GetNumberOfPoints()
    has_rgb = cloud.GetPointData().GetScalars() is not None  # vtkPLYReader stores red/green/blue as scalars
    print(f"Loaded {n} points from {args.ply} ({'RGB' if has_rgb else 'no color'})")

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(cloud)
    if has_rgb:
        mapper.SetColorModeToDirectScalars()
        mapper.ScalarVisibilityOn()
    else:
        mapper.ScalarVisibilityOff()

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetPointSize(args.point_size)
    actor.GetProperty().LightingOff()  # normals in the PLY would otherwise shade the colors

    axes = vtk.vtkAxesActor()

    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.SetBackground(0.1, 0.1, 0.12)
    renderer.ResetCamera()

    text = vtk.vtkTextActor()
    text.SetInput(f"{os.path.basename(args.ply)}  |  {n} points  |  +/- point size, r reset")
    text.GetTextProperty().SetFontSize(14)
    text.SetPosition(10, 10)
    renderer.AddViewProp(text)

    window = vtk.vtkRenderWindow()
    window.AddRenderer(renderer)
    window.SetSize(1024, 768)
    window.SetWindowName("PLY point cloud")

    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(window)
    interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

    orientation = vtk.vtkOrientationMarkerWidget()
    orientation.SetOrientationMarker(axes)
    orientation.SetInteractor(interactor)
    orientation.SetViewport(0.0, 0.8, 0.2, 1.0)
    orientation.EnabledOn()
    orientation.InteractiveOff()

    def on_key(obj, _):
        key = obj.GetKeySym()
        prop = actor.GetProperty()
        if key in ("plus", "equal", "KP_Add"):
            prop.SetPointSize(prop.GetPointSize() + 1)
        elif key in ("minus", "KP_Subtract"):
            prop.SetPointSize(max(1.0, prop.GetPointSize() - 1))
        else:
            return
        window.Render()

    interactor.AddObserver("KeyPressEvent", on_key)

    window.Render()
    interactor.Start()


if __name__ == "__main__":
    main()
