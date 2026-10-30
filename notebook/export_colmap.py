"""Export a VTK volume + transfer function + view file to a COLMAP-style dataset.

Produces (in <out>/sparse/0/):
    points3D.ply   point cloud of voxels made visible by the opacity TF, colored by the color TF
    points3D.bin   same points in COLMAP binary format
    cameras.bin    one PINHOLE camera matching the VTK camera (view angle, window size)
    images.bin     one pose per view in the views .bin (image j -> "<j+1>.png", as SimpleRayCast saves them)

Usage:
    python export_colmap.py chameleon_256x256x256_normalized_space-1.vtk testviews_1_120_1_1.bin \
        --tf chameleon --out ../dataset --images ../vtk/screenShot
"""
import argparse
import os
import shutil
import struct

import numpy as np
import vtk
from vtk.util import numpy_support

# Same control points as the OTF_* / CTF_* macros in vtk/SimpleRayCast.cxx
# OTF: (scalar, opacity)   CTF: (scalar, r, g, b)
TRANSFER_FUNCTIONS = {
    "chameleon": {
        "otf": [(0.0, 0.0), (0.134375, 0.0), (0.175, 0.268018), (0.23125, 0.0), (0.40625, 0.0), (1.0, 1.0)],
        "ctf": [(0.0, 0.02, 0.3813, 0.9981), (0.142857, 0.02, 0.6188, 0.796), (0.238095, 0.02, 0.757035, 0.603735),
                (0.404762, 0.493355, 0.961904, 0.111195), (0.5, 0.999529, 0.999519, 0.0134885),
                (0.952381, 0.798903, 0.0433335, 0.358434), (1.0, 0.6837, 0.05, 0.4139)],
    },
    "flame": {
        "otf": [(0.0, 0.0), (1.0, 1.0)],
        "ctf": [(0.0, 0.18995, 0.07176, 0.23217), (0.0755593, 0.25369, 0.26327, 0.65406),
                (0.141587, 0.27691, 0.44145, 0.91328), (0.210717, 0.23874, 0.61931, 0.99485),
                (0.309764, 0.09532, 0.84455, 0.79299), (0.409599, 0.29042, 0.97403, 0.50321),
                (0.517145, 0.66428, 0.98524, 0.2237), (0.619351, 0.91317, 0.83576, 0.22328),
                (0.728105, 0.99517, 0.57549, 0.16412), (0.821329, 0.91572, 0.3053, 0.05134),
                (0.914552, 0.73661, 0.12477, 0.00769), (0.996117, 0.49321, 0.01963, 0.00955),
                (1.0, 0.4796, 0.01583, 0.01055)],
    },
    "miranda": {
        "otf": [(0.0, 1.0), (0.26, 0.0), (0.42, 0.0), (0.52, 0.6), (0.62, 0.0), (0.76, 0.0), (1.0, 1.0)],
        "ctf": [(0.0, 0.0, 0.9, 0.9), (0.45, 0.0, 0.0, 1.0), (0.5, 0.0, 0.0, 0.5), (0.55, 1.0, 0.0, 0.0),
                (1.0, 1.0, 1.0, 0.0)],
    },
    "beechnut": {
        "otf": [(0.0, 0.0), (0.245059, 0.0), (0.249012, 0.195946), (0.252964, 0.0), (0.264822, 0.0),
                (0.278656, 0.394144), (0.294466, 0.0), (0.310277, 0.0), (0.320158, 0.637387), (1.0, 1.0)],
        "ctf": [(0.0, 0.02, 0.3813, 0.9981), (0.225296, 0.02, 0.72, 0.6574), (0.26087, 0.999529, 0.999519, 0.0134885),
                (0.288538, 1.0, 0.212, 0.988), (0.316206, 0.62, 0.118, 0.988), (1.0, 0.6837, 0.05, 0.4139)],
    },
}


def apply_tf(scalars, tf):
    """Piecewise-linear lookup, identical to vtkPiecewiseFunction / vtkColorTransferFunction defaults (RGB space)."""
    otf = np.array(tf["otf"])
    ctf = np.array(tf["ctf"])
    opacity = np.interp(scalars, otf[:, 0], otf[:, 1])
    rgb = np.stack([np.interp(scalars, ctf[:, 0], ctf[:, c]) for c in (1, 2, 3)], axis=-1)
    return opacity, rgb


def read_volume(path):
    reader = vtk.vtkStructuredPointsReader()
    reader.SetFileName(path)
    reader.Update()
    img = reader.GetOutput()
    nx, ny, nz = img.GetDimensions()
    scalars = numpy_support.vtk_to_numpy(img.GetPointData().GetScalars())
    # VTK point order is x fastest, so a C-order reshape gives [k, j, i]
    return scalars.reshape(nz, ny, nx), np.array(img.GetOrigin()), np.array(img.GetSpacing())


def read_views(path):
    """Same parsing as getSizes()/main() in SimpleRayCast.cxx: name_<block>_<ray>_<sample>_<up>.bin, 9 doubles each."""
    sizes = [int(s) for s in os.path.splitext(os.path.basename(path))[0].split("_")[1:5]]
    return np.fromfile(path, dtype=np.float64).reshape(int(np.prod(sizes)), 9)


def volume_to_points(vol, origin, spacing, tf, min_opacity, max_points, seed):
    opacity, rgb = apply_tf(vol, tf)
    k, j, i = np.nonzero(opacity > min_opacity)
    if max_points and len(i) > max_points:
        # Sample proportionally to opacity so dense regions keep more points
        w = opacity[k, j, i]
        sel = np.random.default_rng(seed).choice(len(i), max_points, replace=False, p=w / w.sum())
        k, j, i = k[sel], j[sel], i[sel]
    xyz = origin + np.stack([i, j, k], axis=-1) * spacing
    colors = np.clip(rgb[k, j, i] * 255.0 + 0.5, 0, 255).astype(np.uint8)
    return xyz, colors


def write_ply(path, xyz, rgb):
    # Same layout as storePly() in 3D Gaussian Splatting (x y z nx ny nz red green blue)
    dtype = [("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("nx", "<f4"), ("ny", "<f4"), ("nz", "<f4"),
             ("red", "u1"), ("green", "u1"), ("blue", "u1")]
    data = np.zeros(len(xyz), dtype=dtype)
    data["x"], data["y"], data["z"] = xyz.T
    data["red"], data["green"], data["blue"] = rgb.T
    header = (f"ply\nformat binary_little_endian 1.0\nelement vertex {len(xyz)}\n"
              + "".join(f"property {'float' if t == '<f4' else 'uchar'} {n}\n" for n, t in dtype)
              + "end_header\n")
    with open(path, "wb") as f:
        f.write(header.encode())
        f.write(data.tobytes())


def write_points3d_bin(path, xyz, rgb):
    with open(path, "wb") as f:
        f.write(struct.pack("<Q", len(xyz)))
        for idx, (p, c) in enumerate(zip(xyz, rgb), start=1):
            # id, xyz, rgb, error, track_length (no 2D observations)
            f.write(struct.pack("<Q3d3BdQ", idx, *p, *c, 0.0, 0))


def vtk_camera_to_colmap(position, focal, up):
    """World-to-camera R, t in COLMAP/OpenCV convention (x right, y down, z forward)."""
    forward = focal - position
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    down = np.cross(forward, right)
    R = np.stack([right, down, forward])
    return R, -R @ position


def rotmat_to_qvec(R):
    w = np.sqrt(max(0.0, 1.0 + R[0, 0] + R[1, 1] + R[2, 2])) / 2
    x = np.sqrt(max(0.0, 1.0 + R[0, 0] - R[1, 1] - R[2, 2])) / 2
    y = np.sqrt(max(0.0, 1.0 - R[0, 0] + R[1, 1] - R[2, 2])) / 2
    z = np.sqrt(max(0.0, 1.0 - R[0, 0] - R[1, 1] + R[2, 2])) / 2
    x = np.copysign(x, R[2, 1] - R[1, 2])
    y = np.copysign(y, R[0, 2] - R[2, 0])
    z = np.copysign(z, R[1, 0] - R[0, 1])
    q = np.array([w, x, y, z])
    return q / np.linalg.norm(q)


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
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("volume", help=".vtk structured points file")
    ap.add_argument("views", help="views .bin written by the view-generation notebook")
    ap.add_argument("--tf", default="chameleon", choices=TRANSFER_FUNCTIONS)
    ap.add_argument("--out", default="dataset")
    ap.add_argument("--images", help="folder with the SimpleRayCast screenshots to copy into <out>/images")
    ap.add_argument("--min-opacity", type=float, default=0.05, help="drop voxels with TF opacity at or below this")
    ap.add_argument("--max-points", type=int, default=200000, help="0 keeps every visible voxel")
    ap.add_argument("--width", type=int, default=256, help="must match renWin->SetSize()")
    ap.add_argument("--height", type=int, default=256)
    ap.add_argument("--view-angle", type=float, default=30.0, help="must match SetViewAngle()")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    sparse = os.path.join(args.out, "sparse", "0")
    os.makedirs(sparse, exist_ok=True)

    print(f"Reading {args.volume} ...")
    vol, origin, spacing = read_volume(args.volume)
    print(f"  shape (z,y,x) {vol.shape}, range [{vol.min():.4f}, {vol.max():.4f}], origin {origin}, spacing {spacing}")

    xyz, rgb = volume_to_points(vol, origin, spacing, TRANSFER_FUNCTIONS[args.tf],
                                args.min_opacity, args.max_points, args.seed)
    print(f"  {len(xyz)} points with TF '{args.tf}'")
    write_ply(os.path.join(sparse, "points3D.ply"), xyz, rgb)
    write_points3d_bin(os.path.join(sparse, "points3D.bin"), xyz, rgb)

    views = read_views(args.views)
    print(f"  {len(views)} views from {args.views}")
    write_cameras_bin(os.path.join(sparse, "cameras.bin"), args.width, args.height, args.view_angle)
    write_images_bin(os.path.join(sparse, "images.bin"), views)

    if args.images:
        dst = os.path.join(args.out, "images")
        os.makedirs(dst, exist_ok=True)
        for j in range(len(views)):
            src = os.path.join(args.images, f"{j + 1}.png")
            if os.path.exists(src):
                shutil.copy(src, dst)
            else:
                print(f"  warning: missing {src}")
    print(f"Done -> {args.out}")


if __name__ == "__main__":
    main()
