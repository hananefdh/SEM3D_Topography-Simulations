# SEM3D_Topography-Simulations

Ce dépôt contient les scripts Python de génération de topographies gaussiennes et les scripts Slurm utilisés pour lancer des simulations de propagation des ondes sismiques avec SEM3D sur ruche 

Prérquis : 
  pour pouvoir lancer le code de simulation il faut avoir installé HexMesh_easyrisk
1. Génération des topographies
   
Le script Python permet de générer une ou plusieurs gaussiennes sur un domaine défini et d'exporter la surface aux formats STL et GT

Exemple 1 : une seule gaussienne

python python/generate_gaussian_topo.py \
    --lx 10000 --ly 10000 \
    --nx 201 --ny 201 \
    --base-z 1500 \
    --sigma-x 1000 --sigma-y 1000 \
    --amplitude 500 \
    --x0-frac 0.5 --y0-frac 0.5 \
    --angle 0 \
    --out dem_gaussian.stl \
    --gts

Exemple 2 : plusieurs gaussiennes

L'option --gaussian peut être répétée. Chaque gaussienne est définie par six valeurs :

x0_frac,y0_frac,sigma_x,sigma_y,amplitude,angle

python python/gaussian_topo_multi.py \
    --lx 10000 --ly 10000 \
    --nx 201 --ny 201 \
    --base-z 1500 \
    --gaussian 0.25,0.50,1000,1000,400,0 \
    --gaussian 0.70,0.65,800,1200,300,30 \
    --out dem_multi_gaussian.stl \
    --gts


Principaux paramètres   

lx, ly -> Dimensions du domaine, en mètres

nx, ny -> Nombre de points de la grille

base-z -> Altitude de base

sigma-x, sigma-y -> Dispersion de la gaussienne

amplitude -> Hauteur ou profondeur du relief

x0-frac, y0-frac -> Position relative du centre

angle -> Orientation en degrés

out -> Nom du fichier STL de sortie

gts -> Génération supplémentaire d'un fichier GTS
