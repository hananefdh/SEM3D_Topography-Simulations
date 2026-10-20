
#!/bin/bash
#SBATCH --job-name=sem3d_gaussian
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=128G
#SBATCH --time=01:30:00
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --output=sem3d_%j.out
#SBATCH --error=sem3d_%j.err

set -Eeuo pipefail

WORKDIR="/gpfs/workdir/fidahh/topographies_sim/gauss_G" #a adapter selon votre repertoitre de travail 
SEM3D="/gpfs/users/fidahh/build2/openacc-stable/SEM3D/sem3d.exe"

module purge
module load nvhpc/26.1/none-none


mpirun -np 1 "$SEM3D"

echo "Simulation SEM3D terminée."

