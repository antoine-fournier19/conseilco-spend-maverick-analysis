import pandas as pd
import numpy as np
from datetime import datetime, timedelta
 
# -----------------------------------------------------------------------------
# 1. CHARGEMENT DES DIMENSIONS
# -----------------------------------------------------------------------------
dim_categories = pd.read_excel('data/dim_categories.xlsx')
dim_entites = pd.read_excel('data/dim_entites.xlsx')
dim_acheteurs = pd.read_excel('data/dim_acheteurs.xlsx')
dim_fournisseurs = pd.read_excel('data/dim_fournisseurs.xlsx')
dim_contrats = pd.read_excel('data/dim_contrats.xlsx')
 
# -----------------------------------------------------------------------------
# 2. PARAMÈTRES DE GÉNÉRATION
# -----------------------------------------------------------------------------
NB_TRANSACTIONS_PAR_AN = {2023: 9000, 2024: 10500, 2025: 10500}
 
POIDS_FAMILLES = {
    'F1': 0.15, 'F2': 0.12, 'F3': 0.35, 'F4': 0.10,
    'F5': 0.06, 'F6': 0.08, 'F7': 0.04, 'F8': 0.10
}
 
RANGES_MONTANTS = {
    'F1': (3000, 80000), 'F2': (500, 25000),
    'F3': (50, 2500),    'F4': (200, 15000),
    'F5': (800, 20000),  'F6': (400, 10000),
    'F7': (2000, 40000), 'F8': (50, 1500)
}
 
TAUX_MAVERICK = {
    ('F1', 2023): 0.28, ('F1', 2024): 0.33, ('F1', 2025): 0.30,
    ('F2', 2023): 0.15, ('F2', 2024): 0.20, ('F2', 2025): 0.18,
    ('F3', 2023): 0.42, ('F3', 2024): 0.48, ('F3', 2025): 0.45,
    ('F4', 2023): 0.08, ('F4', 2024): 0.09, ('F4', 2025): 0.08,
    ('F5', 2023): 0.20, ('F5', 2024): 0.25, ('F5', 2025): 0.22,
    ('F6', 2023): 0.22, ('F6', 2024): 0.28, ('F6', 2025): 0.25,
    ('F7', 2023): 0.10, ('F7', 2024): 0.13, ('F7', 2025): 0.12,
    ('F8', 2023): 0.38, ('F8', 2024): 0.43, ('F8', 2025): 0.40,
}
 
BONUS_LYON = 0.06
BUREAU_LYON = 'BUR-02'
 
PONDERATION_MENSUELLE = [0.90, 0.95, 1.15, 1.00, 1.05, 1.15,
                         0.85, 0.60, 1.15, 1.05, 1.15, 0.80]
 
POIDS_SOUS_FAMILLES_F1 = {
    'SF01': 0.25,
    'SF02': 0.50,
    'SF03': 0.15,
    'SF04': 0.10
}
 
POIDS_PIRATE = {
    'F1': 3,
    'F3': 1.3,
    'F8': 1.1
}
 
# [FIX] Taux de rattachement contrat cadre pour fournisseurs référencés sans contrat dédié
# Contrôle direct de la zone grise : 0.75 → ~55-60% couverture contractuelle
TAUX_RATTACHEMENT_CONTRAT_CADRE = 0.35
 
# -----------------------------------------------------------------------------
# 3. FONCTIONS AUXILIAIRES
# -----------------------------------------------------------------------------
def tirer_date(annee):
    mois = np.random.choice(range(1, 13), p=np.array(PONDERATION_MENSUELLE)/sum(PONDERATION_MENSUELLE))
    jour = np.random.randint(1, 29)
    return datetime(annee, mois, jour)
 
def tirer_famille():
    return np.random.choice(list(POIDS_FAMILLES.keys()), 
                             p=list(POIDS_FAMILLES.values()))
 
def tirer_montant_theorique(famille):
    mini, maxi = RANGES_MONTANTS[famille]
    mu = np.log((mini + maxi) / 4)
    sigma = 0.7
    montant = np.random.lognormal(mu, sigma)
    return np.clip(montant, mini, maxi)
 
def est_maverick(famille, annee, id_bureau):
    taux = TAUX_MAVERICK[(famille, annee)]
    if id_bureau == BUREAU_LYON:
        taux += BONUS_LYON
    return np.random.random() < taux
 
# -----------------------------------------------------------------------------
# 4. PRÉCALCUL DES STRUCTURES UTILES
# -----------------------------------------------------------------------------
ids_pirates = set(
    dim_fournisseurs[dim_fournisseurs['notes'].str.contains('PIRATE', na=False)]['id_fournisseur']
)
 
ids_pirates_f1 = set(
    dim_fournisseurs[
        dim_fournisseurs['notes'].str.contains('PIRATE', na=False) &
        (dim_fournisseurs['famille_principale'] == 'F1')
    ]['id_fournisseur']
)
 
categories_f1 = dim_categories[dim_categories['code_famille'] == 'F1'].copy()
map_sf_f1 = {row['code_sous_famille']: row for _, row in categories_f1.iterrows()}
 
categorie_sf02 = dim_categories[dim_categories['id_categorie'] == 'CAT-002'].iloc[0]
 
# [FIX] Précalcul du mapping code_sous_famille → code_famille pour les contrats cadres
map_sf_to_famille = dict(zip(dim_categories['code_sous_famille'], dim_categories['code_famille']))
dim_contrats['code_famille'] = dim_contrats['code_sous_famille_couverte'].map(map_sf_to_famille)
 
# -----------------------------------------------------------------------------
# 5. BOUCLE DE GÉNÉRATION
# -----------------------------------------------------------------------------
transactions = []
compteur = 1
 
for annee, nb_tx in NB_TRANSACTIONS_PAR_AN.items():
    for _ in range(nb_tx):
        famille = tirer_famille()
 
        centre_cout = dim_entites.sample(1, weights='effectif_estime').iloc[0]
        id_bureau = centre_cout['id_bureau']
 
        acheteurs_bureau = dim_acheteurs[
            dim_acheteurs['id_centre_cout_rattachement'].isin(
                dim_entites[dim_entites['id_bureau'] == id_bureau]['id_centre_cout']
            )
        ]
        acheteur = acheteurs_bureau.sample(1).iloc[0] if len(acheteurs_bureau) > 0 else dim_acheteurs.sample(1).iloc[0]
 
        maverick = est_maverick(famille, annee, id_bureau)
 
        fournisseurs_famille = dim_fournisseurs[dim_fournisseurs['famille_principale'] == famille].copy()
        if maverick:
            fournisseurs_eligibles = fournisseurs_famille[
                fournisseurs_famille['statut_referencement'] == 'Non référencé'
            ].copy()
        else:
            fournisseurs_eligibles = fournisseurs_famille[
                fournisseurs_famille['statut_referencement'] == 'Référencé'
            ].copy()
        if len(fournisseurs_eligibles) == 0:
            fournisseurs_eligibles = fournisseurs_famille.copy()
 
        poids = fournisseurs_eligibles['id_fournisseur'].apply(
            lambda x: POIDS_PIRATE.get(famille, 3) if x in ids_pirates else 1
        )
        fournisseur = fournisseurs_eligibles.sample(1, weights=poids).iloc[0]
 
        est_pirate_f1 = fournisseur['id_fournisseur'] in ids_pirates_f1
 
        if est_pirate_f1:
            sous_famille_ligne = categorie_sf02
        elif famille == 'F1':
            codes_sf = list(POIDS_SOUS_FAMILLES_F1.keys())
            poids_sf = [POIDS_SOUS_FAMILLES_F1[c] for c in codes_sf]
            code_sf_tire = np.random.choice(codes_sf, p=poids_sf)
            sous_famille_ligne = map_sf_f1[code_sf_tire]
        else:
            sous_familles_possibles = dim_categories[dim_categories['code_famille'] == famille]
            sous_famille_ligne = sous_familles_possibles.sample(1).iloc[0]
 
        montant_theorique = tirer_montant_theorique(famille)
        if maverick:
            surcout = np.clip(np.random.normal(0.08, 0.03), 0.03, 0.15)
            montant_ht = montant_theorique * (1 + surcout)
        else:
            montant_ht = montant_theorique
 
        if maverick:
            delai = int(np.clip(np.random.normal(12, 5), 1, 30))
        else:
            delai = int(np.clip(np.random.normal(5, 2), 1, 10))
 
        # [FIX] Rattachement contrat — logique corrigée
        id_contrat = None
        if not maverick:
            # 1. Chercher un contrat dédié au fournisseur (logique inchangée)
            contrats_possibles = dim_contrats[
                (dim_contrats['id_fournisseur'] == fournisseur['id_fournisseur']) &
                (dim_contrats['statut'] == 'Actif')
            ]
            if len(contrats_possibles) > 0:
                id_contrat = contrats_possibles.sample(1).iloc[0]['id_contrat']
            elif fournisseur['statut_referencement'] == 'Référencé':
                # 2. Fournisseur référencé sans contrat dédié → rattacher un contrat cadre
                # de la même famille avec probabilité TAUX_RATTACHEMENT_CONTRAT_CADRE
                contrats_cadre = dim_contrats[
                    (dim_contrats['code_famille'] == famille) &
                    (dim_contrats['statut'] == 'Actif')
                ]
                if len(contrats_cadre) > 0 and np.random.random() < TAUX_RATTACHEMENT_CONTRAT_CADRE:
                    id_contrat = contrats_cadre.sample(1).iloc[0]['id_contrat']
 
        transactions.append({
            'id_transaction': f'TR-{compteur:07d}',
            'date_transaction': tirer_date(annee).strftime('%Y-%m-%d'),
            'id_fournisseur': fournisseur['id_fournisseur'],
            'id_categorie': sous_famille_ligne['id_categorie'],
            'id_centre_cout': centre_cout['id_centre_cout'],
            'id_acheteur': acheteur['id_acheteur'],
            'id_contrat': id_contrat,
            'montant_ht': round(montant_ht, 2),
            'devise': 'EUR',
            'statut_validation': np.random.choice(
                ['Validé', 'En attente', 'Rejeté'],
                p=[0.92, 0.06, 0.02]
            ),
            'delai_traitement_jours': delai,
            'flag_maverick': maverick
        })
        compteur += 1
 
# -----------------------------------------------------------------------------
# 6. EXPORT
# -----------------------------------------------------------------------------
df_faits = pd.DataFrame(transactions)
df_faits.to_csv('fact_depenses.csv', index=False, encoding='utf-8-sig')
print(f"Généré {len(df_faits)} transactions")
