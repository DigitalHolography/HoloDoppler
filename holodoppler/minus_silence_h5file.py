import h5py
import numpy as np

def soustraire_fichiers_h5(fichier_signal, fichier_reference, fichier_sortie):
    def copier_et_soustraire(nom, objet):
        # Cas 1 : C'est un dossier (Group)
        if isinstance(objet, h5py.Group):
            f_out.require_group(nom)
            # Copie des attributs du groupe
            for cle, valeur in objet.attrs.items():
                f_out[nom].attrs[cle] = valeur
                
        # Cas 2 : C'est un tableau de données (Dataset)
        elif isinstance(objet, h5py.Dataset):
            donnees_signal = objet[:]
            
            # On vérifie si la donnée est numérique et si elle existe dans le fichier de référence
            if nom in f_ref and np.issubdtype(objet.dtype, np.number):
                donnees_ref = f_ref[nom][:]
                # Soustraction des matrices
                donnees_resultat = donnees_signal - donnees_ref
                dset = f_out.create_dataset(nom, data=donnees_resultat)
            else:
                # Si ce n'est pas un nombre (ex: string) ou absent de la référence, on copie à l'identique
                dset = f_out.create_dataset(nom, data=donnees_signal)
            
            # Copie des attributs du Dataset
            for cle, valeur in objet.attrs.items():
                dset.attrs[cle] = valeur

    # Ouverture des 3 fichiers simultanément
    with h5py.File(fichier_signal, 'r') as f_sig, \
         h5py.File(fichier_reference, 'r') as f_ref, \
         h5py.File(fichier_sortie, 'w') as f_out:
        
        # Copie des attributs de la racine du fichier
        for cle, valeur in f_sig.attrs.items():
            f_out.attrs[cle] = valeur
            
        # Parcours automatique de toute l'arborescence
        f_sig.visititems(copier_et_soustraire)
        
    print(f"Fichier généré avec succès : {fichier_sortie}")

# ==========================================
# Exécution du code
# ==========================================
chemin_10mV = "donnees_10mV.h5"
chemin_silence = "E:\MusicalBox\mesures2\260715_silence\260715_silence_HD\SH_AVG\h5\SH_AVG_output.h5"
chemin_resultat = "donnees_soustraction_10mV.h5"

soustraire_fichiers_h5(chemin_10mV, chemin_silence, chemin_resultat)