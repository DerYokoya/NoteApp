**Français** | [English](./README.md)

# NoteApp

Un éditeur de texte enrichi modulaire pour ordinateur de bureau, développé avec Python et PyQt6, conçu pour étudier la manière dont les éditeurs de documents réels gèrent l'état, la mise en forme et l'interaction avec l'utilisateur.

---

## Application

[![Télécharger l'application](https://img.shields.io/badge/Download-App-0A192F?style=for-the-badge)](https://github.com/DerYokoya/NoteApp/releases/tag/v1.1.0)<br>

---

## Démonstrations vidéo

### Démonstration générale
https://github.com/user-attachments/assets/d6096059-27d3-41dd-b621-1abeac8861bb

### Tests unitaires
https://github.com/user-attachments/assets/7a42b4c9-5c68-4ed8-b92f-bf14eaff2585

### Persistance / Stockage
https://github.com/user-attachments/assets/6be404e3-19c1-41ae-9288-574617280206

### Insertion d'images
https://github.com/user-attachments/assets/6841fa4d-eaef-4139-94e4-6eda2a43821c

---

## Images

### Captures d'écran 
<div align="center">
  <table>
    <tr>
      <td align="center">
        <img width="250" alt="Fenêtre principale" src="screenshots/screenshot_main.png" /><br />
        <sub><b>Fenêtre principale</b></sub>
      </td>
      <td align="center">
        <img width="250" alt="Mise en forme du texte" src="screenshots/screenshot_formatting.png" /><br />
        <sub><b>Mise en forme du texte</b></sub>
      </td>
      <td align="center">
        <img width="250" alt="Titres" src="screenshots/screenshot_headings.png" /><br />
        <sub><b>Titres</b></sub>
      </td>
    </tr>
    <tr>
      <td align="center">
        <img width="250" alt="Redimensionner l'image" src="screenshots/screenshot_resize.png" /><br />
        <sub><b>Redimensionner l'image</b></sub>
      </td>
      <td align="center">
        <img width="250" alt="Mise en forme du tableau" src="screenshots/screenshot_table_format.png" /><br />
        <sub><b>Mise en forme d'un tableau</b></sub>
      </td>
      <td align="center">
        <img width="250" alt="Barre de recherche" src="screenshots/screenshot_search.png" /><br />
        <sub><b>Barre de recherche</b></sub>
      </td>
    </tr>
    <tr>
      <td align="center">
        <img width="250" alt="Listes" src="screenshots/screenshot_lists.png" /><br />
        <sub><b>Listes</b></sub>
      </td>
      <td align="center">
        <img width="250" alt="Interligne" src="screenshots/screenshot_spacing.png" /><br />
        <sub><b>Interligne</b></sub>
      </td>
      <td align="center">
        <img width="250" alt="Résultat de l'exportation PDF" src="screenshots/pdf_export_result.png" /><br />
        <sub><b>Exportation PDF</b></sub>
      </td>
    </tr>
  </table>
</div>

---

## Présentation

NoteApp est un éditeur de bureau riche en fonctionnalités qui prend en charge les workflows multi-documents, le contenu structuré (tableaux, images) et les sessions persistantes.

L'objectif de ce projet n'était pas seulement de reproduire les fonctionnalités courantes d'un éditeur, mais de **concevoir un système capable de gérer l'état des documents, la cohérence de la mise en forme et les interactions utilisateur à grande échelle**.

---

## Architecture

L'application est structurée autour de la séparation des préoccupations entre l'interface utilisateur, l'état des documents et la persistance :

- **Couche UI (MainWindow / Widgets)**
  - Gère la mise en page, les barres d'outils et les interactions utilisateur
  - Transmet les actions à l'éditeur et à la logique du document
  - Widgets personnalisés : SearchBar, StatusBarWidget, TablePropertiesDialog, TextOrientationDialog

- **Couche Éditeur / Document**
  - Gère l'état du texte, le comportement du curseur et les opérations de mise en forme
  - Encapsule chaque document par onglet à des fins d'isolation

- **Couche de persistance**
  - Gère l'enregistrement et le chargement des documents (HTML et TXT)
  - Garantit la préservation de la mise en forme d'une session à l'autre

- **Gestionnaire de session**
  - Stocke les onglets ouverts et les restaure au démarrage
  - Assure la continuité lors des redémarrages de l'application

---

## Décisions techniques clés

- **HTML comme format de stockage**
  - Choisi pour préserver le texte enrichi, les images et la structure sans avoir à concevoir un format personnalisé

- **Modèle de document multi-onglets**
  - Chaque onglet conserve un état indépendant pour éviter toute interférence entre les documents

- **Conception axée sur le local**
  - Aucune dépendance externe ni intégration au cloud, ce qui garantit performances et fiabilité

- **PyQt6 pour l'interface utilisateur**
  - Permet un contrôle précis des interactions sur le bureau et des widgets complexes

---

## Défis et solutions

- **Cohérence du texte enrichi**
  - La gestion des styles qui se chevauchent (gras, titres, couleurs) sans conflits a nécessité un contrôle minutieux de la mise en forme

- **Manipulation dynamique des tableaux**
  - Prise en charge des mises à jour et de la mise en forme des lignes/colonnes sans altérer l'intégrité de la mise en page

- **Persistance de la session**
  - Garantir que les onglets, les chemins d'accès aux fichiers et l'état de l'interface utilisateur soient restaurés en toute sécurité à chaque redémarrage

- **Synchronisation de l'état**
  - Maintenir la cohérence entre les indicateurs de l'interface utilisateur (par exemple, ● non enregistré) et les modifications réelles du document

---

## Fonctionnalités (sélectionnées)

### Gestion des documents
- Édition multi-onglets avec réorganisation par glisser-déposer
- Récupération de la session au redémarrage
- Prise en charge des fichiers HTML et texte brut
- Ouverture de fichiers par glisser-déposer

### Édition et mise en forme
- Mise en forme de texte enrichi (titres, mise en forme en ligne, couleurs)
- Commandes pour les listes, l'indentation et l'alignement
- Système de mise en forme clair
- Prise en charge des exposants et des indices
- Blocs de code avec mise en forme monospace
- Contrôle de l'interligne (simple, 1,5x, double)

### Contenu structuré
- Tableaux entièrement modifiables (lignes, colonnes, mise en forme)
- Insertion d'images avec redimensionnement et mise à l'échelle
- Création et modification de liens hypertextes (navigation Ctrl+clic)
- Séparateurs de lignes horizontaux

### Navigation et expérience utilisateur
- Recherche et remplacement avec suivi des correspondances
- **Fonctionnalité de remplacement (Ctrl+H)**
- Barre d'état (position du curseur, nombre de mots)
- Flux de travail axé sur le clavier pour toutes les actions principales
- Prise en charge de l'impression avec exportation au format PDF
- **Basculement entre le thème clair et le thème sombre (Ctrl+Maj+D) ; les préférences sont conservées d'une session à l'autre**

---

## Conception du système

L'application est structurée comme un système de bureau en couches où les interactions de l'utilisateur passent de l'interface utilisateur à la logique et à la persistance du document.

### Flux général
```
[Actions de l'utilisateur]
    ↓
(MainWindow)

[MainWindow (app/main_window.py)]
    ↓
    ├─→ gère les raccourcis clavier
    ├─→ gère les clics dans les menus
    ├─→ gère les boutons de la barre d'outils
    ├─→ gère le glisser-déposer
    ↓
    ├─→ _setup_ui
    ├─→ _create_menu_bar
    ├─→ _create_formatting_toolbar
    ├─→ _setup_shortcuts
    └─→ _setup_timers
    ↓
    ├─→ gère la liste des onglets
    ├─→ connecte les signaux
    └─→ gère l'état de l'interface utilisateur
    ↓
    ↓
    ├───────────────┬────────────────┬────────────────┬────────────────┐
    ↓               ↓                ↓                ↓
[models/]     [services/]       [widgets/]        [config/]
    ↓               ↓                ↓                ↓
    │               │                │                │
    │               │                │                └─→ constantes (AppConfig, StyleSheet)
    │               │                │
    │               │                └─→ SearchBar, StatusBarWidget,
    │               │                     TablePropertiesDialog,
    │               │                     
    │               │
    │               └─→ Opérations sur les fichiers (lecture/écriture/suppression),
    │                    Gestionnaire de paramètres (géométrie, fichiers récents, restauration de session)
    │
    └─→ État du document, DocumentTab,
         LinkAwareTextEdit,
         is_modified, mark_saved,
         get_content_html

(modèles/services/widgets/config interagissent tous avec ↓)

[Document Qt (en mémoire)]
    ↓
    ├─→ QTextDocument
    ├─→ pile d'annulation/rétablissement
    ├─→ curseur de texte enrichi
    └─→ images intégrées

[Système de fichiers]
    ↑   ↓
    ├─→ .html
    ├─→ .txt
    ├─→ sauvegardes .bak
    └─→ encodage UTF‑8 / latin‑1

[QSettings]
    ↑   ↓
    ├─→ géométrie de la fenêtre
    ├─→ onglets ouverts
    └─→ fichiers récents

```
---

## Raccourcis clavier

Une liste complète des raccourcis clavier est disponible dans [SHORTCUTS.fr.md](SHORTCUTS.fr.md).

---

## Prise en charge des fichiers

- **HTML (.html)** — Mise en forme et structure entièrement préservées  
- **TXT (.txt)** — Remplacement par du texte brut  
- Détection automatique du mode au chargement  

---

## Ce que ce projet démontre

- Conception d'une **application de bureau avec état**
- Gestion **simultanée de plusieurs documents**
- Gestion de **contenu structuré (tableaux, médias)**
- Création de **systèmes persistants (récupération de session)**
- Création de **workflows d'interface utilisateur réactifs et intuitifs**

---

## Améliorations futures

- **Système de plugins pour l'extensibilité**
- **Optimisation des performances pour les documents volumineux**
- **Refactorisation vers une architecture MVC/MVVM**
- **Plus d'options d'exportation (outre le PDF, qui a déjà été implémenté)**
- **Synchronisation et sauvegarde dans le cloud**
- **Vérification orthographique**
- **Récupération après enregistrement automatique**

---

## Tests

L'application comprend une suite de tests complète utilisant pytest et pytest-qt :

```
# Exécuter tous les tests
pytest tests/ -v

# Exécuter une catégorie de tests spécifique
pytest tests/test_document_tab.py -v

# Exécuter avec un rapport de couverture
pytest tests/ --cov=. --cov-report=html
```

---

## Installation

### Pré-requis
- Python 3.10 ou version ultérieure
- PyQt6
- pytest (facultatif, pour exécuter les tests)

### Configuration
```
git clone https://github.com/DerYokoya/NoteApp.git
cd NoteApp
pip install -r requirements.txt
python main.py

# Exécuter les tests (facultatif)
pip install pytest pytest-qt
pytest tests/ -v
```
