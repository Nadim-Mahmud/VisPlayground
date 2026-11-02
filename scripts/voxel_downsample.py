"""Copy a COLMAP sparse model, replacing its points with a voxel downsampled copy of them.

Uses Open3D voxel_down_sample: one point per occupied VOXEL_SIZE voxel, at the mean position and color of
the points in it.

Produces (in <OUT>/sparse/0/):
    cameras.bin, images.bin   copied from SRC
    points3D.ply, points3D.bin   the downsampled points

Usage: edit the settings below, then run
    python voxel_downsample.py
"""
import os
import shutil
import struct

import numpy as np
import open3d as o3d
import vtk
from vtk.util import numpy_support

from export_colmap import write_ply, write_points3d_bin

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
SRC = os.path.join(BASE, "data", "chameleon_colmap", "sparse", "0")
OUT = os.path.join(BASE, "data", "chameleon_colmap_downsampled")  # output directory for COLMAP-style dataset
VOXEL_SIZE = 5.0  # in world units (volume spacing is 1)


def read_points3d_bin(path):
    """xyz, rgb of a points3D.bin without 2D observations (as export_colmap writes it)."""
    record = np.dtype([("id", "<u8"), ("xyz", "<f8", 3), ("rgb", "u1", 3), ("error", "<f8"), ("track", "<u8")])
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        points = np.fromfile(f, dtype=record, count=n)
    assert len(points) == n and not points["track"].any(), "only points without tracks supported"
    return points["xyz"], points["rgb"]


def voxel_downsample(xyz, rgb, voxel_size):
    pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(xyz))
    pcd.colors = o3d.utility.Vector3dVector(rgb / 255.0)
    down = pcd.voxel_down_sample(voxel_size)
    return np.asarray(down.points), np.round(np.asarray(down.colors) * 255).astype(np.uint8)


def to_polydata(xyz, rgb):
    points = vtk.vtkPoints()
    points.SetData(numpy_support.numpy_to_vtk(xyz.astype(np.float32), deep=True))
    colors = numpy_support.numpy_to_vtk(rgb, deep=True, array_type=vtk.VTK_UNSIGNED_CHAR)
    colors.SetName("RGB")
    poly = vtk.vtkPolyData()
    poly.SetPoints(points)
    poly.GetPointData().SetScalars(colors)
    return poly


def main():
    sparse = os.path.join(OUT, "sparse", "0")
    os.makedirs(sparse, exist_ok=True)

    xyz, rgb = read_points3d_bin(os.path.join(SRC, "points3D.bin"))
    print(f"{len(xyz)} points in {SRC}")
    xyz, rgb = voxel_downsample(xyz, rgb, VOXEL_SIZE)
    print(f"  kept {len(xyz)} with voxel size {VOXEL_SIZE}")
    print(f"  bounds min {xyz.min(0)}, max {xyz.max(0)}")

    for name in ("cameras.bin", "images.bin"):
        shutil.copy2(os.path.join(SRC, name), os.path.join(sparse, name))
    write_ply(os.path.join(sparse, "points3D.ply"), to_polydata(xyz, rgb))
    write_points3d_bin(os.path.join(sparse, "points3D.bin"), xyz, rgb)

    print(f"Done -> {OUT}")


if __name__ == "__main__":
    main()
