# Documentation des mesures DAX — ConseilCo Spend Analysis

> Rapport Power BI — v5 — Mis à jour le 11/05/2026

---

## 01 Volumétrie

Mesures socles. Servent de base à tous les calculs du rapport. Ne pas modifier sans vérifier les dépendances en cascade.

---

### Total dépenses HT
Somme du montant HT de toutes les transactions du périmètre filtré. Mesure de référence pour toutes les analyses de volume.
```dax
SUM ( 'Facturation-Dépenses'[Montant HT] )
```

---

### Nombre de transactions
Nombre total de lignes de la table Dépenses sur le périmètre filtré. Socle pour tous les calculs de fréquence et de taux.
```dax
COUNTROWS ( 'Facturation-Dépenses' )
```

---

### Nombre de fournisseurs distincts
Nombre de fournisseurs uniques ayant transigé sur le périmètre filtré. Mesure non-additive : un fournisseur actif dans plusieurs familles est compté une seule fois au total.
```dax
DISTINCTCOUNT( 'Facturation-Dépenses'[ID Fournisseur] )
```

---

### Nombre d'entités actives
Nombre de centres de coût ayant généré au moins une transaction sur le périmètre filtré.
```dax
DISTINCTCOUNT( 'Facturation-Dépenses'[ID Centre de coût] )
```

---

### Effectif total ConseilCo
Somme des effectifs estimés de toutes les entités. Le filtre `ALL(Calendrier)` supprime le contexte temporel — l'effectif est une donnée statique, indépendante de la période sélectionnée.
```dax
CALCULATE( SUM ( 'Entités'[Effectif estimé] ), ALL( Calendrier ) )
```

---

## 02 Maverick

Mesures de diagnostic du maverick buying. Deux lectures complémentaires : métier (flag) et contractuelle (ID Contrat).

---

### Montant maverick
Somme des montants HT des transactions flaguées Maverick = TRUE. Vision Direction Achats du maverick en valeur absolue.
```dax
CALCULATE( [Total dépenses HT], 'Facturation-Dépenses'[Maverick] = TRUE )
```

---

### Taux maverick métier
Pourcentage de transactions flaguées Maverick = TRUE. Indicateur officiel Direction Achats.
```dax
DIVIDE(
    CALCULATE( [Nombre de transactions], 'Facturation-Dépenses'[Maverick] = TRUE ),
    [Nombre de transactions]
)
```

---

### Taux non-couverture contractuelle
Pourcentage de transactions sans contrat rattaché (ID Contrat vide). Vision pilotage contractuel — indépendante du flag métier.
```dax
DIVIDE(
    CALCULATE( [Nombre de transactions], ISBLANK( 'Facturation-Dépenses'[ID Contrat] ) ),
    [Nombre de transactions]
)
```

---

### Ecart double lecture
Écart entre taux de non-couverture contractuelle et taux maverick métier. Matérialise la **zone grise** : transactions hors cadre contractuel non détectées par le flag. Insight central du projet.
```dax
[Taux non-couverture contractuelle] - [Taux maverick métier]
```

---

### Montant maverick lib *(affichage)*
Montant maverick formaté en millions d'euros pour affichage dans les cartes KPI et annotations.
```dax
FORMAT ( [Montant maverick] / 1000000, "#,##0.00" ) & " M€"
```

---

### Zone grise pts (affichage) *(affichage)*
Écart double lecture formaté en points entiers pour affichage dans la carte KPI "Zone grise" page 1.
```dax
FORMAT( [Ecart double lecture] * 100, "0" ) & " pts"
```

---

### Taux maverick autres bureaux lib *(affichage)*
Taux maverick moyen des bureaux hors Lyon formaté pour annotation comparative page 3. Exclut Lyon du calcul via `ALL + filtre <> Lyon`.
```dax
"vs " & FORMAT(
    CALCULATE( [Taux maverick métier], ALL('Entités'[Bureau]), 'Entités'[Bureau] <> "Lyon" ) * 100,
    "0,0"
) & "% moyenne autres bureaux"
```

---

## 03 Surcoût

Mesures de quantification financière du maverick buying. Hypothèse centrale : la remise moyenne négociée représente le surcoût unitaire des achats hors contrat.

---

### Remise moyenne négociée
Moyenne arithmétique du taux de remise sur l'ensemble des contrats (actifs et inactifs).
> ⚠️ Inclut les contrats Expirés et En renouvellement. Écart avec les actifs seuls négligeable.
```dax
AVERAGE( Contrats[Remise négociée] )
```

---

### Surcoût maverick estimé
Estimation du surcoût généré par le maverick buying : montant maverick × remise moyenne. Hypothèse simplificatrice — la remise moyenne du panel s'applique uniformément.
```dax
[Montant maverick] * [Remise moyenne négociée]
```

---

### Surcoût récupérable best-in-class /3
Économie annuelle récupérable en atteignant le taux de conformité best-in-class marché (référence Ardent Partners CPO Rising). Figée à 0,75 — indépendante du curseur What-if. Divisée par 3 pour ramener sur une base annuelle. KPI signature page 4.
```dax
VAR TauxCibleBenchmark = 0.75
VAR TauxConformiteActuel = 1 - [Taux maverick métier]
VAR PartConvertible = TauxCibleBenchmark - TauxConformiteActuel
RETURN
    IF(
        PartConvertible > 0,
        ( PartConvertible * [Total dépenses HT] * [Remise moyenne négociée] ) / 3,
        0
    )
```

---

### Surcoût par tête lib *(affichage)*
Surcoût maverick annuel par collaborateur, arrondi à la dizaine d'euros. Divise le surcoût total par le nombre d'années et l'effectif total.
```dax
"soit ~" & FORMAT(
    MROUND(
        DIVIDE( [Surcoût maverick estimé], DISTINCTCOUNT( Calendrier[Année] ) * SUM( 'Entités'[Effectif estimé] ) ),
        10
    ),
    "#,##0"
) & " € par collaborateur / an"
```

---

### Surcoût maverick estimé lib *(affichage)*
Surcoût maverick total formaté en millions d'euros pour affichage dans les annotations et sous-titres.
```dax
FORMAT ( [Surcoût maverick estimé] / 1000000, "#,##0.00" ) & " M€"
```

---

## 04 Time intelligence

Mesures temporelles. Nécessitent la table Calendrier marquée comme table de dates. Non utilisées dans le rapport actuel — conservées pour une éventuelle page d'analyse temporelle.

---

### Total dépenses YTD
Cumul des dépenses HT depuis le 1er janvier de l'année courante.
```dax
CALCULATE( [Total dépenses HT], DATESYTD( Calendrier[Date] ) )
```

---

### Total dépenses N-1
Dépenses HT sur la même période, décalée d'un an.
```dax
CALCULATE( [Total dépenses HT], SAMEPERIODLASTYEAR( Calendrier[Date] ) )
```

---

### Variation N vs N-1
Variation relative des dépenses vs année précédente.
```dax
DIVIDE(
    [Total dépenses HT] - [Total dépenses N-1],
    [Total dépenses N-1]
)
```

---

### Taux maverick mois précédent
Taux maverick métier sur le mois précédent le contexte courant.
```dax
CALCULATE( [Taux maverick métier], PREVIOUSMONTH( Calendrier[Date] ) )
```

---

## 05 Cibles & contextuelles

Mesures de comparaison réel vs objectif et d'analyses géographiques.

---

### Taux maverick cible
Taux de maverick cible moyenné sur les sous-familles du contexte filtré. Référence pour les analyses réel vs objectif par famille.
```dax
AVERAGE( 'Catégories'[Taux maverick cible] )
```

---

### Dépenses par tête
Dépense externe moyenne par collaborateur. Indicateur de benchmarking cabinet vs pairs.
```dax
DIVIDE( [Total dépenses HT], [Effectif total ConseilCo] )
```

---

### Surperformance maverick Lyon
Écart entre le taux maverick de Lyon et la moyenne des autres bureaux. Insight central page 3 : Lyon dérive contractuellement, pas budgétairement.
```dax
CALCULATE( [Taux maverick métier], 'Entités'[Bureau] = "Lyon" )
- CALCULATE( [Taux maverick métier], 'Entités'[Bureau] <> "Lyon" )
```

---

### Ecart maverick vs cible
Écart entre taux maverick réel et taux cible. Positif = hors objectif, négatif = sous contrôle. Indicateur de priorisation des actions par famille.
```dax
[Taux maverick métier] - [Taux maverick cible]
```

---

### Écart maverick pts (affichage) *(affichage)*
Écart réel vs cible formaté en points entiers pour affichage dans les cartes KPI famille page 2.
```dax
FORMAT( [Ecart maverick vs cible] * 100, "0" ) & " pts"
```

---

### Surperformance Lyon pts lib *(affichage)*
Écart Lyon vs pairs formaté avec signe + forcé pour affichage dans la carte KPI "Écart vs pairs" page 3.
```dax
FORMAT( [Surperformance maverick Lyon] * 100, "+0.0" ) & " pts"
```

---

### Dépense par tête Lille lib *(affichage)*
Dépense par tête de Lille formatée en K€ pour annotation comparative page 3. Sert à démontrer que Lyon ne dépense pas plus que ses pairs en volume.
```dax
"comparable à Lille (" & FORMAT(
    CALCULATE( [Dépenses par tête], 'Entités'[Bureau] = "Lille" ) / 1000,
    "0"
) & " K€)"
```

---

## 06 Famille 1

Mesures dédiées à l'analyse de F1 Prestations intellectuelles externes — angle mort identifié page 2.

---

### Montant maverick sous titre lib *(affichage)*
Montant maverick F1 formaté en M€ pour sous-titre de la carte KPI "Montant maverick F1" page 2.
```dax
FORMAT(
    CALCULATE( [Montant maverick], 'Catégories'[Famille] = "Prestations intellectuelles externes" ) / 1000000,
    "0.0"
) & " M€ engagés hors contrat"
```

---

### Montant maverick F1 part lib *(affichage)*
Part du surcoût F1 dans le surcoût maverick total, formatée en pourcentage pour sous-texte KPI page 2.
```dax
"soit " & FORMAT(
    DIVIDE(
        CALCULATE( [Surcoût maverick estimé], 'Catégories'[Famille] = "Prestations intellectuelles externes" ),
        CALCULATE( [Surcoût maverick estimé], ALL('Catégories') )
    ) * 100,
    "0"
) & "% du montant d'achat maverick total"
```

---

### Cible réalisé famille 1 lib *(affichage)*
Texte comparatif cible vs réalisé pour F1. Hardcodé sur F1 — insensible aux filtres famille.
```dax
"cible métier " & FORMAT(
    CALCULATE( [Taux maverick cible], 'Catégories'[Famille] = "Prestations intellectuelles externes" ) * 100,
    "0"
) & "% — réalisé " & FORMAT(
    CALCULATE( [Taux maverick métier], 'Catégories'[Famille] = "Prestations intellectuelles externes" ) * 100,
    "0"
) & "%"
```

---

### Top sous-famille F1
Retourne la sous-famille F1 avec l'écart vs cible le plus élevé. Utilisée pour le titre dynamique page 2.
```dax
VAR _table =
    CALCULATETABLE(
        ADDCOLUMNS( VALUES( 'Catégories'[Sous-famille] ), "@ecart", [Ecart maverick vs cible] ),
        'Catégories'[Famille] = "Prestations intellectuelles externes"
    )
RETURN MAXX( TOPN( 1, _table, [@ecart], DESC ), 'Catégories'[Sous-famille] )
```

---

## 07 Plan d'action

Mesures dédiées à la page 4 — leviers, simulateur What-if et KPI globaux.

---

### Fournisseurs à contractualiser
Nombre de fournisseurs non référencés ayant généré des transactions maverick. KPI 2 page 4.
```dax
CALCULATE(
    DISTINCTCOUNT( 'Facturation-Dépenses'[ID Fournisseur] ),
    'Fournisseurs'[Statut référencement] = "Non référencé",
    'Facturation-Dépenses'[Maverick] = TRUE
)
```

---

### Impact contractualisation F1
Surcoût annuel moyen du maverick F1. Représente le potentiel maximum si conformité F1 à 100% — à présenter comme plafond théorique, non comme cible. Levier 1 page 4.
```dax
CALCULATE( [Surcoût maverick estimé], 'Catégories'[Famille] = "Prestations intellectuelles externes" ) / 3
```

---

### Impact gouvernance Lyon
Surcoût annuel moyen du maverick Lyon. Levier 2 page 4.
```dax
CALCULATE( [Surcoût maverick estimé], 'Entités'[Bureau] = "Lyon" ) / 3
```

---

### Économie simulée what-if
Économie estimée sur la période selon le taux de conformité cible sélectionné via le curseur. Pilotée par le paramètre What-if de la table `Taux de conformité cible`.
```dax
( 'Taux de conformité cible'[Valeur Taux de conformité cible] - ( 1 - [Taux maverick métier] ) )
* [Total dépenses HT]
* [Remise moyenne négociée]
```

---

### Valeur Taux de conformité cible
Mesure de lecture du paramètre What-if (table générée via Nouveau paramètre → Plage numérique). Valeur par défaut : conformité actuelle du dataset.
```dax
SELECTEDVALUE( 'Taux de conformité cible'[Taux de conformité cible], 0.68 )
```

---

### Horizon plan lib *(affichage)*
Libellé statique de l'horizon du plan d'action. KPI 3 page 4.
```dax
"24 mois"
```

---

### Horizon détail lib *(affichage)*
Sous-texte statique du KPI Horizon page 4, détaillant les 3 phases du plan d'action.
```dax
"plan en 3 phases : 6 / 12 / 24 mois"
```

---

### Simulation lib *(affichage)*
Phrase narrative dynamique du simulateur What-if page 4. Se met à jour en temps réel selon la position du curseur de conformité cible.
```dax
"Hypothèse : si ConseilCo atteignait " &
FORMAT( 'Taux de conformité cible'[Valeur Taux de conformité cible] * 100, "0" ) &
"% de conformité sur 2023-2025, l'économie estimée serait de " &
FORMAT( [Économie simulée what-if] / 1000000, "0.0" ) &
"M€ sur la période"
```

---

## 08 Affichage

Mesures de titres dynamiques, annotations et footers. Pilotent les visuels contextuels des pages 2 et 3.

---

### Titre sous-familles *(affichage)*
Titre dynamique du graphique sous-familles page 2. Valeur par défaut si aucune famille sélectionnée.
```dax
"Sous-familles - " & SELECTEDVALUE( 'Catégories'[Famille], "Toutes familles" )
```

---

### Titre décomposition bureau *(affichage)*
Titre dynamique du graphique décomposition page 3. Se met à jour selon le bureau sélectionné. Valeur par défaut : Lyon.
```dax
SELECTEDVALUE( 'Entités'[Bureau], "Lyon" ) & " - décomposition du maverick par sous famille"
```

---

### Montant maverick contextuel *(affichage)*
Montant maverick filtré sur le bureau sélectionné. Valeur par défaut : Lyon.
```dax
VAR BureauSelectionne = SELECTEDVALUE( 'Entités'[Bureau], "Lyon" )
RETURN CALCULATE( [Montant maverick], 'Entités'[Bureau] = BureauSelectionne )
```

---

### Annotation Lyon lib *(affichage)*
Phrase d'annotation comparant Lyon à la moyenne ConseilCo globale. Le `ALL('Entités')` supprime le filtre bureau pour calculer la moyenne globale.
```dax
"Lyon dépasse nettement la moyenne ConseilCo (" &
FORMAT( CALCULATE( [Taux maverick métier], ALL('Entités') ) * 100, "0.0" ) &
"%)"
```

---

### Footer décomposition bureau *(affichage)*
Texte de pied de graphique dynamique page 3. Se met à jour selon le bureau sélectionné pour contextualiser le Top 5 sous-familles.
```dax
"Top 5 sous-familles maverick chez " &
SELECTEDVALUE( 'Entités'[Bureau], "Lyon" ) &
" - leviers de contractualisation prioritaires"
```

---

*Documentation générée le 11/05/2026 — ConseilCo Spend Analysis v5*
