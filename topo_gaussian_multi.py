import argparse
import os
import numpy as np
import pyvista as pv


# ============================================================
# Génération de plusieurs Gaussiennes dans un même domaine
# ============================================================

def build_gaussian_grid(
    lx,
    ly,
    nx,
    ny,
    base_z,
    origin_x,
    origin_y,
    gaussians
):
    """
    Génère une topographie composée de plusieurs Gaussiennes.

    Chaque gaussienne est définie par :
        x0_frac, y0_frac, sigma_x, sigma_y, amplitude, angle
    """

    # Coordonnées locales du domaine
    x = np.linspace(0.0, lx, nx)
    y = np.linspace(0.0, ly, ny)

    X, Y = np.meshgrid(x, y)

    # Surface de base
    Z = np.full_like(X, base_z, dtype=float)

    # Ajout des différentes Gaussiennes
    for i, g in enumerate(gaussians, start=1):

        x0_frac = g["x0_frac"]
        y0_frac = g["y0_frac"]
        sigma_x = g["sigma_x"]
        sigma_y = g["sigma_y"]
        amplitude = g["amplitude"]
        angle_deg = g["angle"]

        # Position de la Gaussienne dans le domaine
        x0 = x0_frac * lx
        y0 = y0_frac * ly

        # Coordonnées relatives au centre
        dx = X - x0
        dy = Y - y0

        # Rotation
        theta = np.deg2rad(angle_deg)

        xr = (
            np.cos(theta) * dx
            + np.sin(theta) * dy
        )

        yr = (
            -np.sin(theta) * dx
            + np.cos(theta) * dy
        )

        # Gaussienne
        exponent = -0.5 * (
            (xr / sigma_x) ** 2
            + (yr / sigma_y) ** 2
        )

        gaussian = amplitude * np.exp(exponent)

        # Ajout à la topographie
        Z += gaussian

        print(
            f"Gaussienne {i}: "
            f"x={x0_frac:.2f}, "
            f"y={y0_frac:.2f}, "
            f"sigma_x={sigma_x:.1f} m, "
            f"sigma_y={sigma_y:.1f} m, "
            f"hauteur={amplitude:.1f} m, "
            f"angle={angle_deg:.1f}°"
        )

    # Passage des coordonnées locales aux coordonnées absolues
    X_abs = X + origin_x
    Y_abs = Y + origin_y

    return X_abs, Y_abs, Z


# ============================================================
# Conversion en surface PyVista
# ============================================================

def to_pyvista_surface(X, Y, Z):

    grid = pv.StructuredGrid(X, Y, Z)

    surface = grid.extract_surface(
        algorithm="dataset_surface"
    )

    surface = surface.triangulate()

    return surface


# ============================================================
# Écriture GTS
# ============================================================


def write_gts(path, vertices, faces):

    # Dictionnaire :
    # (sommet_a, sommet_b) -> numéro de l'arête
    edges = {}

    # Liste des arêtes sous forme de couples de sommets
    edge_vertices = []

    # Pour chaque face triangulaire
    face_edges = []

    for face in faces:

        current_face_edges = []

        for i in range(3):

            a = int(face[i])
            b = int(face[(i + 1) % 3])

            # Une arête ne dépend pas de son orientation
            key = tuple(sorted((a, b)))

            if key not in edges:
                edges[key] = len(edge_vertices) + 1
                edge_vertices.append(key)

            current_face_edges.append(edges[key])

        face_edges.append(current_face_edges)

    with open(path, "w", newline="\n") as f:

        # Header GTS
        f.write(
            f"{len(vertices)} "
            f"{len(edge_vertices)} "
            f"{len(faces)} "
            f"GtsSurface GtsFace GtsEdge GtsVertex\n"
        )

        # ------------------------------------------------
        # Sommets
        # ------------------------------------------------
        for vertex in vertices:
            f.write(
                f"{vertex[0]:.12f} "
                f"{vertex[1]:.12f} "
                f"{vertex[2]:.12f}\n"
            )

        # ------------------------------------------------
        # Arêtes
        # ------------------------------------------------
        for a, b in edge_vertices:
            f.write(
                f"{a + 1} {b + 1}\n"
            )

        # ------------------------------------------------
        # Faces
        # ------------------------------------------------
        for e1, e2, e3 in face_edges:
            f.write(
                f"{e1} {e2} {e3}\n"
            )
# ============================================================
# Arguments
# ============================================================

parser = argparse.ArgumentParser(
    description="Génération d'une topographie avec plusieurs Gaussiennes."
)

parser.add_argument("--lx", type=float, default=10000.0)
parser.add_argument("--ly", type=float, default=10000.0)

parser.add_argument("--nx", type=int, default=201)
parser.add_argument("--ny", type=int, default=201)

parser.add_argument("--base-z", type=float, default=1500.0)

parser.add_argument(
    "--origin-x",
    type=float,
    default=0.0
)

parser.add_argument(
    "--origin-y",
    type=float,
    default=0.0
)

# Anciennes options conservées pour compatibilité
parser.add_argument("--sigma-x", type=float, default=1000.0)
parser.add_argument("--sigma-y", type=float, default=1000.0)
parser.add_argument("--amplitude", type=float, default=500.0)
parser.add_argument("--x0-frac", type=float, default=0.5)
parser.add_argument("--y0-frac", type=float, default=0.5)
parser.add_argument("--angle", type=float, default=0.0)

# Nouvelle option permettant plusieurs Gaussiennes
parser.add_argument(
    "--gaussian",
    action="append",
    default=None,
    help=(
        "Gaussienne sous la forme : "
        "x0_frac,y0_frac,sigma_x,sigma_y,amplitude,angle"
    )
)

parser.add_argument(
    "--out",
    type=str,
    default="dem_gaussian.stl"
)

parser.add_argument(
    "--gts",
    action="store_true",
    help="Génère également un fichier GTS."
)

parser.add_argument(
    "--preview",
    action="store_true",
    help="Affiche la topographie."
)

parser.add_argument(
    "--no-preview",
    action="store_true"
)

args = parser.parse_args()


# ============================================================
# Définition des Gaussiennes
# ============================================================

if args.gaussian is not None:

    gaussians = []

    for value in args.gaussian:

        values = [float(v) for v in value.split(",")]

        if len(values) != 6:
            raise ValueError(
                "\nErreur : --gaussian doit contenir exactement "
                "6 valeurs :\n"
                "x0_frac,y0_frac,sigma_x,sigma_y,amplitude,angle\n"
                "\nExemple :\n"
                "--gaussian 0.25,0.75,800,800,300,0"
            )

        gaussians.append({
            "x0_frac": values[0],
            "y0_frac": values[1],
            "sigma_x": values[2],
            "sigma_y": values[3],
            "amplitude": values[4],
            "angle": values[5],
        })

else:

    # Compatibilité avec l'ancien fonctionnement :
    # une seule Gaussienne
    gaussians = [{
        "x0_frac": args.x0_frac,
        "y0_frac": args.y0_frac,
        "sigma_x": args.sigma_x,
        "sigma_y": args.sigma_y,
        "amplitude": args.amplitude,
        "angle": args.angle,
    }]


# ============================================================
# Génération
# ============================================================

X, Y, Z = build_gaussian_grid(
    lx=args.lx,
    ly=args.ly,
    nx=args.nx,
    ny=args.ny,
    base_z=args.base_z,
    origin_x=args.origin_x,
    origin_y=args.origin_y,
    gaussians=gaussians
)


print("\n========================================")
print("Topographie générée")
print("========================================")
print(f"Domaine : {args.lx} m x {args.ly} m")
print(f"Résolution : {args.nx} x {args.ny}")
print(f"Base Z : {args.base_z} m")
print(f"Nombre de Gaussiennes : {len(gaussians)}")
print(f"Z min : {Z.min():.3f} m")
print(f"Z max : {Z.max():.3f} m")
print("========================================\n")


# ============================================================
# Conversion PyVista
# ============================================================

surface = to_pyvista_surface(X, Y, Z)


# ============================================================
# Écriture STL
# ============================================================

surface.save(args.out)

print(f"STL écrit : {args.out}")


# ============================================================
# Écriture GTS
# ============================================================

if args.gts:

    gts_path = os.path.splitext(args.out)[0] + ".gts"

    faces = surface.faces.reshape(-1, 4)[:, 1:4]

    write_gts(
        gts_path,
        surface.points,
        faces
    )

    print(f"GTS écrit : {gts_path}")


# ============================================================
# Aperçu
# ============================================================

if args.preview and not args.no_preview:

    plotter = pv.Plotter()

    plotter.add_mesh(
        surface,
        show_edges=False
    )

    plotter.add_axes()

    plotter.show()