from pathlib import Path

import cv2
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog


# ----------------------------------------------------------------------
# Sélection du fichier
# ----------------------------------------------------------------------

root = tk.Tk()
root.withdraw()

chemin_video = filedialog.askopenfilename(
    title="Sélectionner la vidéo M0",
    filetypes=[
        ("Fichiers vidéo MP4", "*.mp4"),
        ("Tous les fichiers", "*.*"),
    ],
)

root.destroy()

if not chemin_video:
    raise FileNotFoundError("Aucune vidéo M0 sélectionnée.")

FICHIER_VIDEO = Path(chemin_video)


# ----------------------------------------------------------------------
# Paramètres temporels
# ----------------------------------------------------------------------

FREQUENCE_CAMERA = 37_000       # images caméra par seconde
TAILLE_FENETRE = 256            # images caméra par image M0

PAS_TEMPOREL = TAILLE_FENETRE / FREQUENCE_CAMERA


# ----------------------------------------------------------------------
# Nom de l'acquisition
# ----------------------------------------------------------------------

def trouver_nom_acquisition(chemin_video: Path) -> str:
    """
    Récupère le nom de l'acquisition depuis le fichier ou les dossiers.
    """

    nom_fichier = chemin_video.stem

    # Cas : 260716_AUZ_1_HD_M0.mp4
    if nom_fichier.lower() != "m0":
        return nom_fichier.removesuffix("_M0")

    # Cas : .../260716_AUZ_1_HD/SLIDING_SHACK_HARTMANN/mp4/M0.mp4
    dossiers_generiques = {
        "mp4",
        "sliding_shack_hartmann",
        "videos",
        "video",
    }

    for dossier in chemin_video.parents:
        if dossier.name.lower() not in dossiers_generiques:
            return dossier.name

    return nom_fichier


nom_base = trouver_nom_acquisition(FICHIER_VIDEO)

print(f"Vidéo sélectionnée : {FICHIER_VIDEO}")
print(f"Nom de l'acquisition : {nom_base}")


# ----------------------------------------------------------------------
# Paramètres graphiques
# ----------------------------------------------------------------------

plt.rcParams.update({
    "font.size": 14,
    "axes.titlesize": 22,
    "axes.labelsize": 20,
    "xtick.labelsize": 18,
    "ytick.labelsize": 18,
    "legend.fontsize": 18,
})


# ----------------------------------------------------------------------
# Lecture de la vidéo et moyenne de toute l'image
# ----------------------------------------------------------------------

capture = cv2.VideoCapture(str(FICHIER_VIDEO))

if not capture.isOpened():
    raise FileNotFoundError(
        f"Impossible d'ouvrir la vidéo : {FICHIER_VIDEO}"
    )

signal_moyen = []

while True:

    succes, image = capture.read()

    if not succes:
        break

    image_grise = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    ).astype(float)

    # Moyenne de tous les pixels de l'image
    signal_moyen.append(image_grise.mean())

capture.release()

signal_moyen = np.asarray(signal_moyen)

if signal_moyen.size == 0:
    raise RuntimeError(
        f"Aucune image n'a été lue dans {FICHIER_VIDEO.name}."
    )


# ----------------------------------------------------------------------
# Axe temporel
# ----------------------------------------------------------------------

temps = np.arange(signal_moyen.size) * PAS_TEMPOREL

duree_totale = signal_moyen.size * PAS_TEMPOREL

print(f"Nombre d'images M0 : {signal_moyen.size}")
print(f"Pas temporel : {PAS_TEMPOREL * 1000:.3f} ms")
print(f"Durée totale : {duree_totale:.3f} s")
print(
    f"Signal M0 compris entre "
    f"{signal_moyen.min():.3f} et {signal_moyen.max():.3f}"
)


# ----------------------------------------------------------------------
# Tracé
# ----------------------------------------------------------------------

figure, axe = plt.subplots(figsize=(10, 5))

axe.scatter(
    temps,
    signal_moyen,
    s=9,
    color="black",
    label="Spatially averaged M0 signal",
)

axe.set_xlabel("Time (s)")
axe.set_ylabel("Mean M0 signal (a.u.)")


# ----------------------------------------------------------------------
# Limites verticales propres à chaque acquisition
# ----------------------------------------------------------------------

limites_y = {
    "260717_AUZ_HD": (20, 35),
    "260716_AUZ_1_HD": (25, 55),
}

if nom_base in limites_y:
    axe.set_ylim(*limites_y[nom_base])
    print(
        f"Limites verticales appliquées pour {nom_base} : "
        f"{limites_y[nom_base]}"
    )
else:
    print(
        f"Aucune limite verticale définie pour {nom_base}. "
        "Échelle automatique utilisée."
    )

axe.grid(True, alpha=0.6)

figure.tight_layout()


# ----------------------------------------------------------------------
# Sauvegarde
# ----------------------------------------------------------------------

DOSSIER_FIGURES = Path(__file__).parent / "figures"
DOSSIER_FIGURES.mkdir(exist_ok=True)

nom_figure = DOSSIER_FIGURES / f"{nom_base}_mean_M0_signal"

figure.savefig(
    f"{nom_figure}.png",
    dpi=300,
    bbox_inches="tight",
)

figure.savefig(
    f"{nom_figure}.eps",
    format="eps",
    bbox_inches="tight",
)

print(f"Figure PNG enregistrée : {nom_figure}.png")
print(f"Figure EPS enregistrée : {nom_figure}.eps")

plt.show()