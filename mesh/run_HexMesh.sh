#!/bin/bash
#SBATCH --job-name=hexmesh
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --output=hexmesh_%j.out
#SBATCH --error=hexmesh_%j.err

set -Eeuo pipefail

module purge
module load gcc/15.1.0/gcc-15.1.0
module load openmpi/4.1.8/gcc-15.1.0
module load cmake/3.31.9/gcc-15.1.0
module load boost/1.89.0/gcc-15.1.0
module load cgal/6.0.2/intel-oneapi-compilers-2025.3.1


# Répertoire contenant Hexmesh.input et les fichiers de topographie
WORKDIR="..."
cd "$WORKDIR"
# Vérification du fichier d'entrée
if [[ ! -f "HexMesh.input" ]]; then
    echo "Erreur : le fichier HexMesh.input est introuvable dans $(pwd)" >&2
    exit 1
fi
#lancement de l'executable HexMesh_easyrisk ( à adapter selon votre repertoire)

/workdir/fidahh/topographies_sim/HexMesh_easyrisk/hexmesh
