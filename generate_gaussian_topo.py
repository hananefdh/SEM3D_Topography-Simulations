#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_gaussian_topo.py
=========================

Genere une topographie synthetique en cloche gaussienne avec controle
complet de sa geometrie :

    - amplitude       : hauteur du relief
    - base_z          : altitude de base
    - x0_frac/y0_frac : position du centre
    - sigma_x         : largeur selon l'axe principal X
    - sigma_y         : largeur selon l'axe principal Y
    - angle           : orientation de la colline dans le plan XY

La gaussienne peut donc etre :

    - circulaire       : sigma_x = sigma_y
    - elliptique       : sigma_x != sigma_y
    - orientee         : angle != 0

Formule :

    z(x,y) = base_z + amplitude *
             exp(-0.5 * ((xr/sigma_x)^2 + (yr/sigma_y)^2))

avec rotation :

    xr =  cos(theta) * dx + sin(theta) * dy
    yr = -sin(theta) * dx + cos(theta) * dy

ou :

    dx = x - x0
    dy = y - y0

Le maillage est genere avec pyvista puis exporte en STL.
Un GTS peut egalement etre genere directement.

Exemples
--------

1) Colline ronde :

    python3 generate_gaussian_topo.py \
        --lx 10000 --ly 10000 \
        --sigma-x 1000 --sigma-y 1000 \
        --amplitude 500 \
        --base-z 1500 \
        --x0-frac 0.5 --y0-frac 0.5 \
        --angle 0 \
        --origin-x 339142.39 \
        --origin-y 5089971.33 \
        --nx 201 --ny 201 \
        --out dem_gaussian.stl \
        --gts

2) Colline allongee selon X :

    --sigma-x 2000 --sigma-y 700

3) Colline allongee selon Y :

    --sigma-x 700 --sigma-y 2000

4) Colline elliptique tournee de 45 degres :

    --sigma-x 2000 --sigma-y 700 --angle 45

5) Centre decale :

    --x0-frac 0.35 --y0-frac 0.65

Dependances
-----------
    pip install pyvista numpy matplotlib
"""

import argparse
import os

import numpy as np
import pyvista as pv


# --------------------------------------------------------------------------
# Construction de la topographie gaussienne
# --------------------------------------------------------------------------

def build_gaussian_grid(
    lx,
    ly,
    nx,
    ny,
    sigma_x,
    sigma_y,
    amplitude,
    base_z,
    x0_frac,
    y0_frac,
    angle_deg,
):
    """
    Construit une gaussienne 2D elliptique eventuellement tournee.

    Parametres
    ----------
    lx, ly : float
        Dimensions du domaine.

    nx, ny : int
        Nombre de points de grille.

    sigma_x, sigma_y : float
        Ecarts-types selon les deux axes principaux de la colline.

    amplitude : float
        Hauteur maximale au-dessus de base_z.

    base_z : float
        Altitude de reference.

    x0_frac, y0_frac : float
        Position du centre en fraction du domaine.

    angle_deg : float
        Angle de rotation dans le plan XY, en degres.
        Convention :
            0 deg   -> axe sigma_x selon X
            90 deg  -> axe sigma_x selon Y
    """

    x = np.linspace(0.0, lx, nx)
    y = np.linspace(0.0, ly, ny)

    X, Y = np.meshgrid(x, y, indexing="xy")

    # Centre de la colline
    x0 = x0_frac * lx
    y0 = y0_frac * ly

    # Coordonnees relatives au centre
    dx = X - x0
    dy = Y - y0

    # Rotation
    theta = np.deg2rad(angle_deg)

    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)

    xr = cos_theta * dx + sin_theta * dy
    yr = -sin_theta * dx + cos_theta * dy

    # Gaussienne elliptique
    exponent = -0.5 * (
        (xr / sigma_x) ** 2 +
        (yr / sigma_y) ** 2
    )

    Z = base_z + amplitude * np.exp(exponent)

    return X, Y, Z


# --------------------------------------------------------------------------
# Conversion PyVista
# --------------------------------------------------------------------------

def to_pyvista_surface(X, Y, Z):
    """
    StructuredGrid -> surface triangulee.
    """

    grid = pv.StructuredGrid(X, Y, Z)

    surf = grid.extract_surface(
        algorithm="dataset_surface"
    )

    surf = surf.triangulate()

    return surf


# --------------------------------------------------------------------------
# Ecriture GTS
# --------------------------------------------------------------------------

def write_gts(path, vertices, faces):
    """
    Ecrit un fichier GTS standard.

    vertices : (Nv, 3)
    faces    : (Nf, 3)

    Les indices d'entree sont 0-based.
    Les indices ecrits dans le GTS sont 1-based.
    """

    # Trois aretes par triangle
    e0 = np.sort(faces[:, [0, 1]], axis=1)
    e1 = np.sort(faces[:, [1, 2]], axis=1)
    e2 = np.sort(faces[:, [2, 0]], axis=1)

    all_edges = np.concatenate(
        [e0, e1, e2],
        axis=0
    )

    # Suppression des doublons
    uniq_edges, inv = np.unique(
        all_edges,
        axis=0,
        return_inverse=True
    )

    inv = inv.reshape(3, -1).T

    with open(path, "w") as f:

        f.write(
            f"{len(vertices)} "
            f"{len(uniq_edges)} "
            f"{len(faces)} "
            f"GtsSurface GtsFace GtsEdge GtsVertex\n"
        )

        # Sommets
        for v in vertices:
            f.write(
                f"{v[0]:.6f} "
                f"{v[1]:.6f} "
                f"{v[2]:.6f}\n"
            )

        # Aretes
        for e in uniq_edges:
            f.write(
                f"{e[0] + 1} "
                f"{e[1] + 1}\n"
            )

        # Faces
        for tri_edges in inv:
            f.write(
                f"{tri_edges[0] + 1} "
                f"{tri_edges[1] + 1} "
                f"{tri_edges[2] + 1}\n"
            )


# --------------------------------------------------------------------------
# Apercu 2D
# --------------------------------------------------------------------------

def save_preview(
    X,
    Y,
    Z,
    sigma_x,
    sigma_y,
    angle_deg,
    amplitude,
    base_z,
    path,
):
    """
    Genere un apercu 2D :

        gauche : carte topographique
        droite : coupe passant par le centre selon X
    """

    import matplotlib

    matplotlib.use("Agg")

    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(
        1,
        2,
        figsize=(12, 5)
    )

    # --------------------------------------------------------------
    # Vue de dessus
    # --------------------------------------------------------------

    im = ax1.pcolormesh(
        X,
        Y,
        Z,
        shading="auto",
        cmap="terrain"
    )

    ax1.set_aspect("equal")

    ax1.set_xlabel("x (m)")
    ax1.set_ylabel("y (m)")

    ax1.set_title(
        "Topographie gaussienne"
    )

    fig.colorbar(
        im,
        ax=ax1,
        label="z (m)"
    )

    # --------------------------------------------------------------
    # Coupe centrale selon X
    # --------------------------------------------------------------

    j0 = Z.shape[0] // 2

    ax2.plot(
        X[j0, :],
        Z[j0, :]
    )

    ax2.set_xlabel("x (m)")
    ax2.set_ylabel("z (m)")

    ax2.set_title(
        "Coupe au centre selon X"
    )

    ax2.grid(
        True,
        ls=":",
        alpha=0.6
    )

    # --------------------------------------------------------------
    # Informations geometrie
    # --------------------------------------------------------------

    info = (
        f"sigma_x = {sigma_x:.0f} m\n"
        f"sigma_y = {sigma_y:.0f} m\n"
        f"angle = {angle_deg:.1f} deg\n"
        f"amplitude = {amplitude:.0f} m"
    )

    ax1.text(
        0.02,
        0.98,
        info,
        transform=ax1.transAxes,
        verticalalignment="top",
        bbox=dict(
            boxstyle="round",
            facecolor="white",
            alpha=0.8
        )
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=140
    )

    plt.close(fig)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():

    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # --------------------------------------------------------------
    # Domaine
    # --------------------------------------------------------------

    ap.add_argument(
        "--lx",
        type=float,
        required=True,
        help="Largeur du domaine en X (m)"
    )

    ap.add_argument(
        "--ly",
        type=float,
        required=True,
        help="Largeur du domaine en Y (m)"
    )

    ap.add_argument(
        "--nx",
        type=int,
        default=200,
        help="Nombre de points de grille en X"
    )

    ap.add_argument(
        "--ny",
        type=int,
        default=200,
        help="Nombre de points de grille en Y"
    )

    # --------------------------------------------------------------
    # Geometrie de la colline
    # --------------------------------------------------------------

    ap.add_argument(
        "--sigma-x",
        type=float,
        required=True,
        help="Ecart-type selon l'axe principal X (m)"
    )

    ap.add_argument(
        "--sigma-y",
        type=float,
        required=True,
        help="Ecart-type selon l'axe principal Y (m)"
    )

    ap.add_argument(
        "--angle",
        type=float,
        default=0.0,
        help=(
            "Angle de rotation de la colline dans le plan XY "
            "(degres, defaut=0)"
        )
    )

    ap.add_argument(
        "--amplitude",
        type=float,
        default=500.0,
        help="Hauteur du pic au-dessus de base-z (m)"
    )

    ap.add_argument(
        "--base-z",
        type=float,
        default=0.0,
        help="Altitude de base (m)"
    )

    # --------------------------------------------------------------
    # Position du centre
    # --------------------------------------------------------------

    ap.add_argument(
        "--x0-frac",
        type=float,
        default=0.5,
        help=(
            "Position du centre en X, fraction du domaine "
            "(defaut=0.5)"
        )
    )

    ap.add_argument(
        "--y0-frac",
        type=float,
        default=0.5,
        help=(
            "Position du centre en Y, fraction du domaine "
            "(defaut=0.5)"
        )
    )

    # --------------------------------------------------------------
    # Coordonnees UTM
    # --------------------------------------------------------------

    ap.add_argument(
        "--origin-x",
        type=float,
        default=0.0,
        help="Offset UTM ajoute a X (m)"
    )

    ap.add_argument(
        "--origin-y",
        type=float,
        default=0.0,
        help="Offset UTM ajoute a Y (m)"
    )

    # --------------------------------------------------------------
    # Sorties
    # --------------------------------------------------------------

    ap.add_argument(
        "--out",
        default="dem_gaussian.stl",
        help="Fichier STL de sortie"
    )

    ap.add_argument(
        "--gts",
        action="store_true",
        help="Ecrit aussi un GTS directement"
    )

    ap.add_argument(
        "--preview",
        default=None,
        help="PNG d'apercu"
    )

    ap.add_argument(
        "--no-preview",
        action="store_true",
        help="Ne pas generer l'apercu"
    )

    args = ap.parse_args()

    # --------------------------------------------------------------
    # Verification des parametres
    # --------------------------------------------------------------

    if args.sigma_x <= 0:
        ap.error("--sigma-x doit etre > 0")

    if args.sigma_y <= 0:
        ap.error("--sigma-y doit etre > 0")

    if args.nx < 2:
        ap.error("--nx doit etre >= 2")

    if args.ny < 2:
        ap.error("--ny doit etre >= 2")

    if not (0.0 <= args.x0_frac <= 1.0):
        ap.error("--x0-frac doit etre compris entre 0 et 1")

    if not (0.0 <= args.y0_frac <= 1.0):
        ap.error("--y0-frac doit etre compris entre 0 et 1")

    # --------------------------------------------------------------
    # Informations
    # --------------------------------------------------------------

    x0 = args.x0_frac * args.lx
    y0 = args.y0_frac * args.ly

    print()
    print("==============================================")
    print("  GENERATION TOPOGRAPHIE GAUSSIENNE")
    print("==============================================")

    print(
        f"Domaine       : "
        f"{args.lx:.1f} x {args.ly:.1f} m"
    )

    print(
        f"Grille        : "
        f"{args.nx} x {args.ny}"
    )

    print(
        f"Centre local  : "
        f"x={x0:.1f} m, y={y0:.1f} m"
    )

    print(
        f"Sigma X       : "
        f"{args.sigma_x:.1f} m"
    )

    print(
        f"Sigma Y       : "
        f"{args.sigma_y:.1f} m"
    )

    print(
        f"Angle         : "
        f"{args.angle:.2f} deg"
    )

    print(
        f"Amplitude     : "
        f"{args.amplitude:.1f} m"
    )

    print(
        f"Base Z        : "
        f"{args.base_z:.1f} m"
    )

    print(
        f"Sommet        : "
        f"{args.base_z + args.amplitude:.1f} m"
    )

    print(
        f"Rapport sigma : "
        f"sigma_x/sigma_y = "
        f"{args.sigma_x / args.sigma_y:.3f}"
    )

    print()

    # --------------------------------------------------------------
    # Creation du repertoire
    # --------------------------------------------------------------

    out_dir = os.path.dirname(
        os.path.abspath(args.out)
    )

    os.makedirs(
        out_dir,
        exist_ok=True
    )

    # --------------------------------------------------------------
    # Generation
    # --------------------------------------------------------------

    X, Y, Z = build_gaussian_grid(
        args.lx,
        args.ly,
        args.nx,
        args.ny,
        args.sigma_x,
        args.sigma_y,
        args.amplitude,
        args.base_z,
        args.x0_frac,
        args.y0_frac,
        args.angle,
    )

    # --------------------------------------------------------------
    # Apercu
    # --------------------------------------------------------------

    if not args.no_preview:

        prev = (
            args.preview
            or args.out.rsplit(".", 1)[0] + "_preview.png"
        )

        save_preview(
            X,
            Y,
            Z,
            args.sigma_x,
            args.sigma_y,
            args.angle,
            args.amplitude,
            args.base_z,
            prev,
        )

        print(
            f"Apercu : {prev}"
        )

    # --------------------------------------------------------------
    # Ajout des coordonnees UTM
    # --------------------------------------------------------------

    Xg = X + args.origin_x
    Yg = Y + args.origin_y

    # --------------------------------------------------------------
    # Construction surface
    # --------------------------------------------------------------

    print(
        "Construction de la surface avec PyVista..."
    )

    surf = to_pyvista_surface(
        Xg,
        Yg,
        Z
    )

    print(
        f"  {surf.n_points} sommets"
    )

    print(
        f"  {surf.n_cells} triangles"
    )

    # --------------------------------------------------------------
    # STL
    # --------------------------------------------------------------

    surf.save(
        args.out
    )

    print(
        f"STL ecrit : {args.out}"
    )

    print(
        f"Conversion habituelle : "
        f"stl2gts < {args.out} > dem.gts"
    )

    # --------------------------------------------------------------
    # GTS direct
    # --------------------------------------------------------------

    if args.gts:

        gts_path = (
            args.out.rsplit(".", 1)[0]
            + ".gts"
        )

        faces = (
            surf.faces.reshape(-1, 4)[:, 1:4]
        )

        write_gts(
            gts_path,
            surf.points,
            faces
        )

        print(
            f"GTS ecrit directement : "
            f"{gts_path}"
        )

    print()
    print("Generation terminee.")
    print()


if __name__ == "__main__":
    main()