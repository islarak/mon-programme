import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import sqlite3
import os
from tkinter import filedialog 
from calendar import monthrange

# --- Nom de l'entreprise ---
NOM_ENTREPRISE = "O'Délice"

# --- Données avec prix TTC (TVA 5.5% incluse) ---
prix_articles = {
    "Tacos": {1: 6.50, 2: 8.50, 3: 10.50},
    "Tacos Gratiné": {1: 7.50, 2: 9.50, 3: 12.50},
    "Burger": {"Seul": 5, "Double": 6.50, "Triple": 8},
    "Chicken Burger": {"Seul": 6, "Menu": 8},
    "O'Delice Burger": {"Seul": 6, "Menu": 8},
    "Kebab": {"Seul": 5.5, "Menu": 7.5},
    
    # NOUVELLE CATÉGORIE SANDWICH AVEC LES PRIX DU MENU
    "SANDWICH": {
        "O'Delice": 7.50, 
        "Radical": 9.00, 
        "Original": 9.00, 
        "Chicken": 7.00,
        "Américan": 7.00, 
        "Panini": 5.50, 
        "Triple Steack": 8.50
    },
    # FIN NOUVELLE CATÉGORIE
    
    "BOX": {"BOX": 7.50},
    "SALADE O'DÉLICE": {"SALADE O'DÉLICE": 7.00},
    "Assiette": {1: 12, 2: 14, 3: 16},
    "Tex-Mex": {"6 Nuggets": 5, "4 Tenders": 6, "6 Oignon Rings": 5, "6 Cheese Rings": 5, "6 Jalapenos": 5},
    "Menu Enfant": {
        "Burger + Frite + Capri Sun": 6.50,
        "4 Nuggets + Frite + Capri Sun": 6.50,
        "2 Tenders + Frite + Capri Sun": 6.50
    },
    "Frites": {"Moyenne": 3, "Grande": 5},
    "Dessert": {"Tarte au Daim": 2.50, "Tiramisu": 2.50},
    "Boisson": {"Café": 1.20, "Thé": 1.20, "Eau": 1.20, "Capri Sun": 1.20, "Canette": 1.20, "RedBull": 2.50}  # MODIFICATION : Ajout de RedBull
}

# Liste des sous-menus pour la catégorie SANDWICH
sous_menus_sandwich = list(prix_articles["SANDWICH"].keys())

# Liste des types de burgers pour la nouvelle catégorie BURGER
sous_menus_burger = ["Burger", "Chicken Burger", "O'Delice Burger"]

# Liste des types de tacos pour la nouvelle catégorie TACOS
sous_menus_tacos = ["Tacos", "Tacos Gratiné"]

# Options pour la BOX
viandes_box = ["Cordon bleu", "Viande hachée", "Steak", "Poulet mariné", "Tenders", "Nuggets", "Falafel"]

# Liste complète des sauces
sauces_box = ["Ketchup", "Samourai", "Mayonnaise", "Biggy", "Curry", "Blanche", 
              "Andalouse", "Algerienne", "Marocaine", "Barbecue", "Bresilienne"]

viandes_dispo = ["Kebab", "Poulet mariné", "Steack", "Kefta",
                 "Cordon Bleu", "Tenders", "Nuggets", "Falafel"]

# Liste complète des sauces avec "Aucune" en premier
sauces_dispo = ["Aucune", "Ketchup", "Samourai", "Mayonnaise", "Biggy", "Curry", "Blanche", 
                "Andalouse", "Algerienne", "Marocaine", "Barbecue", "Bresilienne"]

supplements_dispo = ["Vache qui rit", "Cheddar", "Mozarella", "Oeuf",
                     "Chèvre", "Raclette", "Fromage Emmental"]

# --- Variables globales ---
nom_client = ""
mode_commande = ""
commande = []
total = 0.0
page_index = 0

# --- Styles ---
TOUCH_BUTTON_STYLE = {
    "font": ("Arial", 18, "bold"),
    "height": 3,
    "width": 20,
    "border": 8,
    "relief": "raised",
    "activebackground": "#cccccc"
}

ACTION_BUTTON_STYLE = {
    "font": ("Arial", 14, "bold"),
    "height": 2,
    "width": 15,
    "border": 5
}

# --- Fonction pour créer des boutons tactiles ---
def creer_bouton_tactile(parent, texte, commande, **kwargs):
    style = TOUCH_BUTTON_STYLE.copy()
    style.update(kwargs)
    return tk.Button(parent, text=texte, command=commande, **style)

# --- Fonction pour mettre à jour l'heure ---
def mettre_a_jour_heure():
    maintenant = datetime.now()
    date_str = maintenant.strftime("%d/%m/%Y")
    heure_str = maintenant.strftime("%H:%M:%S")
    lbl_date_heure.config(text=f"Date: {date_str} | Heure: {heure_str}")
    root.after(1000, mettre_a_jour_heure)

# --- Fonction pour nouvelle commande ---
def nouvelle_commande():
    global commande, total, nom_client, mode_commande, page_index
    
    if commande: 
        reponse = messagebox.askyesno("Nouvelle commande", 
                                     "Voulez-vous vraiment commencer une nouvelle commande?\nLa commande actuelle sera perdue.")
        if not reponse:
            return
    
    # Réinitialiser toutes les variables
    commande = []
    total = 0.0
    nom_client = ""
    mode_commande = ""
    
    # Réinitialiser l'interface
    entry_nom.delete(0, tk.END)
    liste.delete(0, tk.END)
    lbl_total.config(text="Total : 0 €")
    lbl_client.config(text="")
    
    # Retourner à la page 1 (Index 0)
    afficher_page(0)
    
    messagebox.showinfo("Nouvelle commande", "Nouvelle commande prête! Veuillez saisir le numéro de beeper.")

# -----------------
# --- Base de données ---
# -----------------
def init_db():
    try:
        # Utilisation de NOM_ENTREPRISE pour le répertoire des données
        dir_name = NOM_ENTREPRISE.replace("'", "").replace(" ", "") 
        
        if os.name == 'nt': 
            data_dir = os.path.join(os.getenv('APPDATA'), dir_name)
        else: 
            data_dir = os.path.join(os.path.expanduser("~"), f".{dir_name.lower()}")
            
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        db_path = os.path.join(data_dir, "commandes.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS commandes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      nom_client TEXT,
                      mode_commande TEXT,
                      articles TEXT,
                      total REAL,
                      date_commande TEXT)''')
        conn.commit()
        conn.close()
        return db_path
    except Exception as e:
        print(f"Erreur DB: {e}")
        return None

def sauvegarder_db():
    if not commande or not nom_client or not mode_commande:
        return False
    
    articles_str = "\n".join([f"{item['article']} - {item['prix']}€ | {item['details']}" for item in commande])
    
    try:
        db_path = init_db()
        if not db_path:
            messagebox.showerror("Erreur", "Chemin de base de données non trouvé ou non accessible.")
            return False

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("INSERT INTO commandes (nom_client, mode_commande, articles, total, date_commande) VALUES (?, ?, ?, ?, ?)",
                  (nom_client, mode_commande, articles_str, total, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur sauvegarde: {str(e)}")
        return False

def get_db_path():
    dir_name = NOM_ENTREPRISE.replace("'", "").replace(" ", "") 
    if os.name == 'nt': 
        data_dir = os.path.join(os.getenv('APPDATA'), dir_name)
    else: 
        data_dir = os.path.join(os.path.expanduser("~"), f".{dir_name.lower()}")
        
    db_path = os.path.join(data_dir, "commandes.db")
    if os.path.exists(db_path):
        return db_path
    return None

def calculer_tva(montant_ttc):
    """Calcule la TVA 5.5% à partir d'un montant TTC"""
    tva = montant_ttc * (5.5 / 100)
    return round(tva, 2)

def generer_contenu_ticket():
    """Génère le contenu textuel du ticket en format condensé avec TVA incluse."""
    if not commande or not nom_client or not mode_commande:
        return None, "Erreur: Commande, nom client ou mode manquant."
        
    maintenant = datetime.now()
    date_heure = maintenant.strftime("%d/%m/%Y %H:%M:%S")
    SEP = "="*30

    total_ttc = total
    tva_montant = calculer_tva(total_ttc)

    ticket_content = f"""
{SEP}
      {NOM_ENTREPRISE.upper()}
Perpignan/ Fix: 04.68.34.41.61
{SEP}
Date: {date_heure}
Beeper: {nom_client}
Mode: {mode_commande}
{SEP}
{'*' * 30}
     *** COMMANDE ***
{'*' * 30}
"""
    
    # Regrouper les articles identiques avec incrémentation
    articles_groupes = {}
    for item in commande:
        cle = f"{item['article']}|{item['details']}"
        if cle in articles_groupes:
            articles_groupes[cle]['quantite'] += 1
        else:
            articles_groupes[cle] = {
                'article': item['article'],
                'details': item['details'],
                'prix': item['prix'],
                'quantite': 1
            }
    
    # Afficher les articles groupés avec numérotation incrémentée
    numero_ligne = 1
    for cle, item in articles_groupes.items():
        quantite = item['quantite']
        prix_unitaire = item['prix']
        prix_total = prix_unitaire * quantite
        
        ticket_content += f" {numero_ligne} - QTé x {quantite} -- {item['article']} - {prix_total:.2f}€\n"
        
        details = item['details']
        if "Choix:" in details:
            choix = details.split("Choix: ")[1].split(" |")[0]
            ticket_content += f"     Choix: {choix}\n"
        if "Sauce:" in details:
            sauce = details.split("Sauce: ")[1].split(" |")[0]
            ticket_content += f"     Sauce: {sauce}\n"
        if "Viande:" in details:
            viande = details.split("Viande: ")[1].split(" |")[0]
            ticket_content += f"     Viande: {viande}\n"
        if "Taille:" in details:
            taille = details.split("Taille: ")[1].split(" |")[0]
            ticket_content += f"     Taille: {taille}\n"
        
        ticket_content += f"{'-'*40}\n"
        numero_ligne += 1
    
    ticket_content += f"""
{SEP}
TOTAL TTC: {total_ttc:.2f} €
Dont TVA 5.5%: {tva_montant:.2f} €
{SEP}
Merci pour votre commande !
À bientôt !
{SEP}
"""
    return ticket_content, None

# --- OPTIONS AVEC SUPPRESSION DE COMMANDES ---
def afficher_options():
    """Affiche la fenêtre des options avec suppression de commandes"""
    options_win = tk.Toplevel(root)
    options_win.title("Options - Gestion des Commandes")
    options_win.geometry("500x400")
    options_win.config(bg="#f4f4f4")
    
    tk.Label(options_win, text="⚙️ OPTIONS", font=("Arial", 20, "bold"), 
             bg="#f4f4f4", fg="#2c3e50").pack(pady=20)
    
    # Frame pour les boutons d'options
    options_frame = tk.Frame(options_win, bg="#f4f4f4")
    options_frame.pack(pady=20)
    
    # Bouton pour supprimer des commandes
    btn_supprimer = creer_bouton_tactile(options_frame, "🗑️ Supprimer des Commandes", 
                                       lambda: afficher_suppression_commandes(), 
                                       bg="#e74c3c", fg="white", font=("Arial", 14), height=2, width=25)
    btn_supprimer.pack(pady=10)
    
    # Bouton pour vider toute la base de données
    btn_vider_tout = creer_bouton_tactile(options_frame, "💥 Vider Toutes les Commandes", 
                                        lambda: vider_toutes_commandes(), 
                                        bg="#c0392b", fg="white", font=("Arial", 14), height=2, width=25)
    btn_vider_tout.pack(pady=10)
    
    # Bouton pour informations sur la base de données
    btn_info_db = creer_bouton_tactile(options_frame, "📊 Informations Base de Données", 
                                     lambda: afficher_info_db(), 
                                     bg="#3498db", fg="white", font=("Arial", 14), height=2, width=25)
    btn_info_db.pack(pady=10)

def afficher_suppression_commandes():
    """Affiche l'interface pour supprimer des commandes"""
    suppression_win = tk.Toplevel(root)
    suppression_win.title("Supprimer des Commandes")
    suppression_win.geometry("900x600")
    suppression_win.config(bg="#f4f4f4")
    
    tk.Label(suppression_win, text="🗑️ SUPPRIMER DES COMMANDES", font=("Arial", 18, "bold"), 
             bg="#f4f4f4", fg="#2c3e50").pack(pady=10)
    
    # Frame de recherche
    recherche_frame = tk.Frame(suppression_win, bg="#f4f4f4")
    recherche_frame.pack(pady=10, fill="x", padx=20)
    
    tk.Label(recherche_frame, text="Rechercher par numéro de beeper:", font=("Arial", 12), 
             bg="#f4f4f4").pack(side="left", padx=5)
    
    entry_recherche = tk.Entry(recherche_frame, font=("Arial", 12), width=25)
    entry_recherche.pack(side="left", padx=5)
    
    btn_rechercher = tk.Button(recherche_frame, text="🔍 Rechercher", 
                              command=lambda: rechercher_commandes_suppression(tree, entry_recherche.get()),
                              font=("Arial", 10), bg="#3498db", fg="white")
    btn_rechercher.pack(side="left", padx=5)
    
    btn_tout_afficher = tk.Button(recherche_frame, text="📋 Afficher Tout", 
                                 command=lambda: afficher_toutes_commandes(tree),
                                 font=("Arial", 10), bg="#2ecc71", fg="white")
    btn_tout_afficher.pack(side="left", padx=5)
    
    # Frame pour la liste des commandes
    liste_frame = tk.Frame(suppression_win)
    liste_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    # Treeview pour afficher les commandes
    columns = ("ID", "Beeper", "Mode", "Total", "Date")
    tree = ttk.Treeview(liste_frame, columns=columns, show="headings", height=15)
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    
    tree.column("Beeper", width=150)
    tree.column("Date", width=150)
    
    # Scrollbar
    scrollbar = ttk.Scrollbar(liste_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Frame pour les boutons d'action
    action_frame = tk.Frame(suppression_win, bg="#f4f4f4")
    action_frame.pack(pady=10, fill="x", padx=20)
    
    btn_supprimer_selection = tk.Button(action_frame, text="🗑️ Supprimer la Sélection", 
                                       command=lambda: supprimer_commande_selectionnee(tree),
                                       font=("Arial", 12), bg="#e74c3c", fg="white", width=20)
    btn_supprimer_selection.pack(side="left", padx=10)
    
    btn_supprimer_par_date = tk.Button(action_frame, text="📅 Supprimer par Date", 
                                      command=lambda: supprimer_par_date(),
                                      font=("Arial", 12), bg="#e67e22", fg="white", width=20)
    btn_supprimer_par_date.pack(side="left", padx=10)
    
    btn_fermer = tk.Button(action_frame, text="Fermer", 
                          command=suppression_win.destroy,
                          font=("Arial", 12), bg="#7f8c8d", fg="white", width=15)
    btn_fermer.pack(side="right", padx=10)
    
    # Afficher toutes les commandes au démarrage
    afficher_toutes_commandes(tree)

def rechercher_commandes_suppression(tree, nom_recherche):
    """Recherche des commandes pour la suppression"""
    try:
        db_path = get_db_path()
        if not db_path:
            messagebox.showerror("Erreur", "Base de données non trouvée.")
            return
            
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        if nom_recherche.strip():
            c.execute("SELECT * FROM commandes WHERE nom_client LIKE ? ORDER BY date_commande DESC", 
                     (f'%{nom_recherche}%',))
        else:
            c.execute("SELECT * FROM commandes ORDER BY date_commande DESC")
            
        resultats = c.fetchall()
        conn.close()
        
        # Vider le treeview
        for item in tree.get_children():
            tree.delete(item)
        
        # Remplir avec les résultats
        for row in resultats:
            tree.insert("", "end", values=(
                row[0],  # ID
                row[1],  # Beeper
                row[2],  # Mode
                f"{row[4]:.2f} €",  # Total
                row[5]   # Date
            ))
            
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de la recherche: {str(e)}")

def afficher_toutes_commandes(tree):
    """Affiche toutes les commandes dans le treeview"""
    rechercher_commandes_suppression(tree, "")

def supprimer_commande_selectionnee(tree):
    """Supprime la commande sélectionnée"""
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("Erreur", "Veuillez sélectionner une commande à supprimer.")
        return
    
    # Récupérer l'ID de la commande sélectionnée
    item = tree.item(selection[0])
    commande_id = item['values'][0]
    client_nom = item['values'][1]
    date_commande = item['values'][4]
    
    # Confirmation de suppression
    reponse = messagebox.askyesno("Confirmation", 
                                 f"Voulez-vous vraiment supprimer la commande #{commande_id} ?\n"
                                 f"Beeper: {client_nom}\n"
                                 f"Date: {date_commande}\n\n"
                                 f"Cette action est irréversible!")
    
    if reponse:
        try:
            db_path = get_db_path()
            if not db_path:
                messagebox.showerror("Erreur", "Base de données non trouvée.")
                return
                
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("DELETE FROM commandes WHERE id = ?", (commande_id,))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Succès", f"Commande #{commande_id} supprimée avec succès!")
            
            # Actualiser l'affichage
            afficher_toutes_commandes(tree)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la suppression: {str(e)}")

def supprimer_par_date():
    """Supprime les commandes par date"""
    date_win = tk.Toplevel(root)
    date_win.title("Supprimer par Date")
    date_win.geometry("400x300")
    date_win.config(bg="#f4f4f4")
    
    tk.Label(date_win, text="Supprimer les commandes d'une date spécifique:", 
             font=("Arial", 14, "bold"), bg="#f4f4f4").pack(pady=20)
    
    # Frame pour la sélection de date
    date_frame = tk.Frame(date_win, bg="#f4f4f4")
    date_frame.pack(pady=20)
    
    tk.Label(date_frame, text="Date (JJ/MM/AAAA) :", font=("Arial", 12), 
             bg="#f4f4f4").pack(pady=5)
    
    entry_date = tk.Entry(date_frame, font=("Arial", 14), width=15)
    entry_date.pack(pady=10)
    entry_date.insert(0, datetime.now().strftime('%d/%m/%Y'))
    
    def valider_suppression_date():
        date_str = entry_date.get().strip()
        try:
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            date_sql = date_obj.strftime('%Y-%m-%d')
            
            # Compter le nombre de commandes à supprimer
            db_path = get_db_path()
            if not db_path:
                messagebox.showerror("Erreur", "Base de données non trouvée.")
                return
                
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM commandes WHERE date(date_commande) = date(?)", (date_sql,))
            nb_commandes = c.fetchone()[0]
            conn.close()
            
            if nb_commandes == 0:
                messagebox.showinfo("Information", f"Aucune commande trouvée pour la date {date_str}")
                return
            
            # Confirmation de suppression
            reponse = messagebox.askyesno("Confirmation", 
                                         f"Voulez-vous vraiment supprimer {nb_commandes} commande(s) du {date_str} ?\n\n"
                                         f"Cette action est irréversible!")
            
            if reponse:
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute("DELETE FROM commandes WHERE date(date_commande) = date(?)", (date_sql,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Succès", f"{nb_commandes} commande(s) du {date_str} supprimée(s) avec succès!")
                date_win.destroy()
                
        except ValueError:
            messagebox.showerror("Erreur", "Format de date invalide. Utilisez JJ/MM/AAAA")
    
    btn_valider = tk.Button(date_win, text="Supprimer les Commandes", command=valider_suppression_date,
                           font=("Arial", 12), bg="#e74c3c", fg="white", width=20)
    btn_valider.pack(pady=20)

def vider_toutes_commandes():
    """Vide toute la base de données des commandes"""
    reponse = messagebox.askyesno("CONFIRMATION CRITIQUE", 
                                 "⚠️ ATTENTION - ACTION IRRÉVERSIBLE !\n\n"
                                 "Voulez-vous vraiment supprimer TOUTES les commandes ?\n\n"
                                 "Cette action supprimera définitivement toutes les données "
                                 "et ne pourra pas être annulée!")
    
    if reponse:
        try:
            db_path = get_db_path()
            if not db_path:
                messagebox.showerror("Erreur", "Base de données non trouvée.")
                return
                
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("DELETE FROM commandes")
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Succès", "Toutes les commandes ont été supprimées avec succès!")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la suppression: {str(e)}")

def afficher_info_db():
    """Affiche les informations sur la base de données"""
    try:
        db_path = get_db_path()
        if not db_path:
            messagebox.showerror("Erreur", "Base de données non trouvée.")
            return
            
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Compter le nombre total de commandes
        c.execute("SELECT COUNT(*) FROM commandes")
        nb_commandes = c.fetchone()[0]
        
        # Calculer le chiffre d'affaire total
        c.execute("SELECT SUM(total) FROM commandes")
        ca_total = c.fetchone()[0] or 0
        
        # Date de la première commande
        c.execute("SELECT MIN(date_commande) FROM commandes")
        premiere_commande = c.fetchone()[0] or "Aucune"
        
        # Date de la dernière commande
        c.execute("SELECT MAX(date_commande) FROM commandes")
        derniere_commande = c.fetchone()[0] or "Aucune"
        
        conn.close()
        
        # Afficher les informations
        info_win = tk.Toplevel(root)
        info_win.title("Informations Base de Données")
        info_win.geometry("500x400")
        info_win.config(bg="#f4f4f4")
        
        tk.Label(info_win, text="📊 INFORMATIONS BASE DE DONNÉES", 
                font=("Arial", 18, "bold"), bg="#f4f4f4", fg="#2c3e50").pack(pady=20)
        
        # Frame pour les informations
        info_frame = tk.Frame(info_win, bg="#f4f4f4")
        info_frame.pack(pady=20, fill="x", padx=20)
        
        infos = [
            ("📁 Chemin de la base:", db_path),
            ("📦 Nombre total de commandes:", f"{nb_commandes} commande(s)"),
            ("💰 Chiffre d'affaire total:", f"{ca_total:.2f} €"),
            ("📅 Première commande:", premiere_commande),
            ("📆 Dernière commande:", derniere_commande)
        ]
        
        for texte, valeur in infos:
            frame_info = tk.Frame(info_frame, bg="#f4f4f4")
            frame_info.pack(fill="x", pady=8)
            
            tk.Label(frame_info, text=texte, font=("Arial", 12, "bold"), 
                    bg="#f4f4f4", width=25, anchor="w").pack(side="left")
            tk.Label(frame_info, text=valeur, font=("Arial", 12), 
                    bg="#ecf0f1", width=30, anchor="w").pack(side="right")
        
        btn_fermer = tk.Button(info_win, text="Fermer", command=info_win.destroy,
                              font=("Arial", 12), bg="#3498db", fg="white", width=15)
        btn_fermer.pack(pady=20)
        
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de la récupération des informations: {str(e)}")

# --- FONCTIONNALITÉ : STATISTIQUES ---
def afficher_statistiques():
    """Affiche la fenêtre de sélection des statistiques"""
    stats_win = tk.Toplevel(root)
    stats_win.title("Statistiques - Chiffre d'Affaire")
    stats_win.geometry("500x400")
    stats_win.config(bg="#f4f4f4")
    
    tk.Label(stats_win, text="📊 STATISTIQUES", font=("Arial", 20, "bold"), 
             bg="#f4f4f4", fg="#2c3e50").pack(pady=20)
    
    # Frame pour les boutons de choix
    choix_frame = tk.Frame(stats_win, bg="#f4f4f4")
    choix_frame.pack(pady=20)
    
    # Boutons pour les différentes statistiques
    btn_jour = creer_bouton_tactile(choix_frame, "📅 Chiffre d'Affaire Jour", 
                                   lambda: afficher_ca_jour(), 
                                   bg="#3498db", fg="white", font=("Arial", 14), height=2, width=25)
    btn_jour.pack(pady=10)
    
    btn_semaine = creer_bouton_tactile(choix_frame, "📆 Chiffre d'Affaire Semaine", 
                                      lambda: afficher_ca_semaine(), 
                                      bg="#2ecc71", fg="white", font=("Arial", 14), height=2, width=25)
    btn_semaine.pack(pady=10)
    
    btn_mois = creer_bouton_tactile(choix_frame, "📊 Chiffre d'Affaire Mois", 
                                   lambda: afficher_ca_mois(), 
                                   bg="#e67e22", fg="white", font=("Arial", 14), height=2, width=25)
    btn_mois.pack(pady=10)
    
    btn_date_perso = creer_bouton_tactile(choix_frame, "🔍 Chiffre d'Affaire Date Spécifique", 
                                         lambda: afficher_ca_date_perso(), 
                                         bg="#9b59b6", fg="white", font=("Arial", 14), height=2, width=25)
    btn_date_perso.pack(pady=10)

def get_commandes_par_periode(date_debut, date_fin):
    """Récupère les commandes entre deux dates"""
    try:
        db_path = get_db_path()
        if not db_path:
            return []
            
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM commandes WHERE date(date_commande) BETWEEN date(?) AND date(?) ORDER BY date_commande",
                  (date_debut, date_fin))
        resultats = c.fetchall()
        conn.close()
        return resultats
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de la récupération des données: {str(e)}")
        return []

def calculer_statistiques(commandes):
    """Calcule les statistiques à partir d'une liste de commandes"""
    if not commandes:
        return 0, 0, 0
    
    total_ca = sum(commande[4] for commande in commandes)  # commande[4] = total
    nb_commandes = len(commandes)
    panier_moyen = total_ca / nb_commandes if nb_commandes > 0 else 0
    
    return total_ca, nb_commandes, panier_moyen

def afficher_ca_jour():
    """Affiche le chiffre d'affaire du jour"""
    aujourdhui = datetime.now().strftime('%Y-%m-%d')
    commandes = get_commandes_par_periode(aujourdhui, aujourdhui)
    total_ca, nb_commandes, panier_moyen = calculer_statistiques(commandes)
    
    afficher_resultats_stats("JOUR", aujourdhui, aujourdhui, total_ca, nb_commandes, panier_moyen, commandes)

def afficher_ca_semaine():
    """Affiche le chiffre d'affaire de la semaine"""
    aujourdhui = datetime.now()
    debut_semaine = (aujourdhui - timedelta(days=aujourdhui.weekday())).strftime('%Y-%m-%d')
    fin_semaine = aujourdhui.strftime('%Y-%m-%d')
    
    commandes = get_commandes_par_periode(debut_semaine, fin_semaine)
    total_ca, nb_commandes, panier_moyen = calculer_statistiques(commandes)
    
    afficher_resultats_stats("SEMAINE", debut_semaine, fin_semaine, total_ca, nb_commandes, panier_moyen, commandes)

def afficher_ca_mois():
    """Affiche le chiffre d'affaire du mois"""
    aujourdhui = datetime.now()
    debut_mois = aujourdhui.replace(day=1).strftime('%Y-%m-%d')
    fin_mois = aujourdhui.strftime('%Y-%m-%d')
    
    commandes = get_commandes_par_periode(debut_mois, fin_mois)
    total_ca, nb_commandes, panier_moyen = calculer_statistiques(commandes)
    
    afficher_resultats_stats("MOIS", debut_mois, fin_mois, total_ca, nb_commandes, panier_moyen, commandes)

def afficher_ca_date_perso():
    """Affiche le chiffre d'affaire pour une date spécifique"""
    date_win = tk.Toplevel(root)
    date_win.title("Chiffre d'Affaire - Date Spécifique")
    date_win.geometry("400x300")
    date_win.config(bg="#f4f4f4")
    
    tk.Label(date_win, text="Sélectionnez une date :", font=("Arial", 16, "bold"), 
             bg="#f4f4f4").pack(pady=20)
    
    # Frame pour la sélection de date
    date_frame = tk.Frame(date_win, bg="#f4f4f4")
    date_frame.pack(pady=20)
    
    tk.Label(date_frame, text="Date (JJ/MM/AAAA) :", font=("Arial", 12), 
             bg="#f4f4f4").pack(pady=5)
    
    entry_date = tk.Entry(date_frame, font=("Arial", 14), width=15)
    entry_date.pack(pady=10)
    entry_date.insert(0, datetime.now().strftime('%d/%m/%Y'))
    
    def valider_date():
        date_str = entry_date.get().strip()
        try:
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            date_sql = date_obj.strftime('%Y-%m-%d')
            date_win.destroy()
            
            commandes = get_commandes_par_periode(date_sql, date_sql)
            total_ca, nb_commandes, panier_moyen = calculer_statistiques(commandes)
            
            afficher_resultats_stats("DATE SPÉCIFIQUE", date_sql, date_sql, total_ca, nb_commandes, panier_moyen, commandes)
            
        except ValueError:
            messagebox.showerror("Erreur", "Format de date invalide. Utilisez JJ/MM/AAAA")
    
    btn_valider = tk.Button(date_win, text="Valider", command=valider_date,
                           font=("Arial", 12), bg="#3498db", fg="white", width=15)
    btn_valider.pack(pady=20)

def afficher_resultats_stats(periode, date_debut, date_fin, total_ca, nb_commandes, panier_moyen, commandes):
    """Affiche les résultats des statistiques"""
    resultat_win = tk.Toplevel(root)
    resultat_win.title(f"Résultats - {periode}")
    resultat_win.geometry("700x600")
    resultat_win.config(bg="#f4f4f4")
    
    # En-tête
    tk.Label(resultat_win, text=f"📊 CHIFFRE D'AFFAIRE - {periode}", 
             font=("Arial", 18, "bold"), bg="#f4f4f4", fg="#2c3e50").pack(pady=10)
    
    tk.Label(resultat_win, text=f"Période: {date_debut} au {date_fin}", 
             font=("Arial", 12), bg="#f4f4f4").pack(pady=5)
    
    # Frame pour les indicateurs
    indicateurs_frame = tk.Frame(resultat_win, bg="#f4f4f4")
    indicateurs_frame.pack(pady=20, fill="x", padx=20)
    
    # Indicateurs
    indicateurs = [
        ("💰 Chiffre d'Affaire Total", f"{total_ca:.2f} €", "#27ae60"),
        ("📦 Nombre de Commandes", str(nb_commandes), "#3498db"),
        ("🛒 Panier Moyen", f"{panier_moyen:.2f} €", "#e67e22")
    ]
    
    for texte, valeur, couleur in indicateurs:
        frame_ind = tk.Frame(indicateurs_frame, bg="#f4f4f4")
        frame_ind.pack(fill="x", pady=8)
        
        tk.Label(frame_ind, text=texte, font=("Arial", 12, "bold"), 
                bg="#f4f4f4", width=25, anchor="w").pack(side="left")
        tk.Label(frame_ind, text=valeur, font=("Arial", 12, "bold"), 
                bg=couleur, fg="white", width=15).pack(side="right")
    
    # Détail des commandes
    if commandes:
        tk.Label(resultat_win, text="📋 DÉTAIL DES COMMANDES", 
                font=("Arial", 14, "bold"), bg="#f4f4f4").pack(pady=(30, 10))
        
        # Frame avec scrollbar pour les commandes
        frame_commandes = tk.Frame(resultat_win)
        frame_commandes.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Treeview pour afficher les commandes
        columns = ("ID", "Beeper", "Mode", "Total", "Date")
        tree = ttk.Treeview(frame_commandes, columns=columns, show="headings", height=10)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        tree.column("Beeper", width=120)
        tree.column("Date", width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_commandes, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Remplir le treeview
        for commande in commandes:
            tree.insert("", "end", values=(
                commande[0],  # ID
                commande[1],  # Beeper
                commande[2],  # Mode
                f"{commande[4]:.2f} €",  # Total
                commande[5]   # Date
            ))
    else:
        tk.Label(resultat_win, text="Aucune commande trouvée pour cette période", 
                font=("Arial", 12), bg="#f4f4f4", fg="#7f8c8d").pack(pady=20)

# --- Fonctions d'action ---

def afficher_ticket_client():
    """Affiche le contenu du ticket dans une nouvelle fenêtre pour vérification."""
    content, erreur = generer_contenu_ticket()
    
    if erreur:
        messagebox.showwarning("Erreur", erreur)
        return
        
    ticket_win = tk.Toplevel(root)
    ticket_win.title(f"Ticket client - {nom_client}")
    ticket_win.geometry("400x600") 
    ticket_win.transient(root) 

    tk.Label(ticket_win, text="APERÇU DU TICKET", font=("Arial", 18, "bold")).pack(pady=10)

    frame_text = tk.Frame(ticket_win)
    frame_text.pack(fill="both", expand=True, padx=20, pady=10)
    
    scrollbar = tk.Scrollbar(frame_text)
    scrollbar.pack(side="right", fill="y")
    
    # Police Courier pour le formatage du ticket
    text_widget = tk.Text(frame_text, wrap="none", font=("Courier", 12), yscrollcommand=scrollbar.set)
    text_widget.insert(tk.END, content)
    text_widget.config(state="disabled") 
    text_widget.pack(side="left", fill="both", expand=True)
    
    scrollbar.config(command=text_widget.yview)

    tk.Button(ticket_win, text="Fermer", command=ticket_win.destroy, 
              font=("Arial", 12), bg="#e74c3c", fg="white", width=15).pack(pady=10)

def traiter_impression_sauvegarde():
    """
    Génère le ticket au format .txt, le sauvegarde, et tente de l'imprimer 
    (via la commande système sur Windows).
    """
    content, erreur = generer_contenu_ticket()
    
    if erreur:
        messagebox.showwarning("Erreur", erreur)
        return

    maintenant = datetime.now()
    
    # Ouvre la boîte de dialogue "Enregistrer sous"
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Fichiers texte", "*.txt")],
        title="Enregistrer le ticket client",
        initialfile=f"ticket_{nom_client}_{maintenant.strftime('%Y%m%d_%H%M%S')}.txt"
    )
    
    # Si l'utilisateur clique sur Annuler dans la boîte de dialogue, on quitte.
    if not file_path:
        return
    
    try:
        # 1. Sauvegarde du fichier
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 2. Sauvegarde de la commande dans la DB
        if not sauvegarder_db(): 
            messagebox.showwarning("Alerte", "La commande a été enregistrée sur le disque, mais la sauvegarde en base de données a échoué.")
        
        # 3. Tentative d'impression via la commande système
        if os.name == 'nt': # Windows (la méthode la plus fiable)
            os.startfile(file_path, "print") 
            messagebox.showinfo("Succès", f"Ticket enregistré, sauvegardé et envoyé à l'imprimante!")
        else: # Linux/Mac (l'impression automatique est plus complexe, on notifie de l'enregistrement)
            messagebox.showinfo("Succès", f"Ticket enregistré et sauvegardé! (Impression manuelle requise)")

        # Démarrer une nouvelle commande après impression/sauvegarde
        nouvelle_commande() 
        
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de l'enregistrement ou de l'impression: {str(e)}")

def rechercher_commandes():
    def afficher_resultats():
        nom_recherche = entry_recherche.get().strip()
        if not nom_recherche:
            messagebox.showwarning("Erreur", "Veuillez entrer un numéro de beeper à rechercher.")
            return
        
        try:
            db_path = get_db_path()
            if not db_path:
                messagebox.showerror("Erreur", "Base de données non trouvée.")
                return
                
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT * FROM commandes WHERE nom_client LIKE ? ORDER BY date_commande DESC", (f'%{nom_recherche}%',))
            resultats = c.fetchall()
            conn.close()
            
            for item in tree.get_children():
                tree.delete(item)
            
            for row in resultats:
                tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la recherche: {str(e)}")
    
    def voir_details():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Erreur", "Veuillez sélectionner une commande.")
            return
        
        item = tree.item(selection[0])
        details = item['values']
        
        detail_win = tk.Toplevel(recherche_win)
        detail_win.title(f"Détails de la commande #{details[0]}")
        detail_win.geometry("600x400")
        
        tk.Label(detail_win, text=f"Commande #{details[0]}", font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(detail_win, text=f"Beeper: {details[1]}", font=("Arial", 12)).pack(anchor="w", padx=20)
        tk.Label(detail_win, text=f"Mode: {details[2]}", font=("Arial", 12)).pack(anchor="w", padx=20)
        tk.Label(detail_win, text=f"Date: {details[5]}", font=("Arial", 12)).pack(anchor="w", padx=20)
        
        tk.Label(detail_win, text="Articles:", font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        
        frame_articles = tk.Frame(detail_win)
        frame_articles.pack(fill="both", expand=True, padx=20, pady=5)
        
        scrollbar = tk.Scrollbar(frame_articles)
        scrollbar.pack(side="right", fill="y")
        
        text_articles = tk.Text(frame_articles, yscrollcommand=scrollbar.set)
        text_articles.pack(side="left", fill="both", expand=True)
        text_articles.insert("1.0", details[3])
        text_articles.config(state="disabled")
        
        scrollbar.config(command=text_articles.yview)
        
        tk.Label(detail_win, text=f"Total: {details[4]} €", font=("Arial", 14, "bold")).pack(anchor="e", padx=20, pady=10)
    
    recherche_win = tk.Toplevel(root)
    recherche_win.title("Rechercher des commandes")
    recherche_win.geometry("800x500")
    
    tk.Label(recherche_win, text="Rechercher par numéro de beeper:", font=("Arial", 14)).pack(pady=10)
    
    frame_recherche = tk.Frame(recherche_win)
    frame_recherche.pack(pady=5)
    
    entry_recherche = tk.Entry(frame_recherche, font=("Arial", 12), width=30)
    entry_recherche.pack(side="left", padx=5)
    
    btn_rechercher = tk.Button(frame_recherche, text="🔍 Rechercher", command=afficher_resultats)
    btn_rechercher.pack(side="left", padx=5)
    
    frame_resultats = tk.Frame(recherche_win)
    frame_resultats.pack(fill="both", expand=True, padx=10, pady=10)
    
    columns = ("ID", "Beeper", "Mode", "Articles", "Total", "Date")
    tree = ttk.Treeview(frame_resultats, columns=columns, show="headings", height=10)
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    
    tree.column("Articles", width=200)
    tree.column("Date", width=120)
    
    scrollbar = ttk.Scrollbar(frame_resultats, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    btn_details = tk.Button(recherche_win, text="Voir détails", command=voir_details, bg="#3498db", fg="white")
    btn_details.pack(pady=10)

def sauvegarder_commande():
    if not commande:
        messagebox.showwarning("Erreur", "Aucune commande à sauvegarder.")
        return
    
    if sauvegarder_db():
        messagebox.showinfo("Succès", "Commande sauvegardée!")
        nouvelle_commande()

def quitter_application():
    """
    Ferme l'application avec confirmation d'enregistrement.
    Propose de sauvegarder la commande en cours avant de quitter.
    """
    # Vérifier s'il y a une commande en cours qui peut être sauvegardée
    if commande and nom_client and mode_commande:
        reponse = messagebox.askyesnocancel(
            "Quitter l'application", 
            f"Voulez-vous enregistrer la commande de {nom_client} avant de quitter?\n\n"
            f"Total : {total:.2f} €\n"
            f"Nombre d'articles : {len(commande)}\n\n"
            "• Oui : Enregistrer et quitter\n"
            "• Non : Quitter sans enregistrer\n"
            "• Annuler : Rester dans l'application"
        )
        
        if reponse is None:  # Annuler - ne rien faire
            return
        elif reponse:  # Oui - Enregistrer avant de quitter
            if sauvegarder_db():
                messagebox.showinfo("Succès", f"Commande de {nom_client} enregistrée avec succès!\nTotal : {total:.2f} €")
            else:
                messagebox.showerror("Erreur", "Erreur lors de l'enregistrement de la commande!")
    
    # Si pas de commande en cours ou si l'utilisateur a choisi "Non"
    elif commande:  # Commande incomplète (il manque nom ou mode)
        reponse = messagebox.askyesno(
            "Commande incomplète",
            "La commande en cours n'est pas complète (numéro de beeper ou mode manquant).\n\n"
            "Voulez-vous vraiment quitter sans enregistrer?",
            icon="warning"
        )
        if not reponse:
            return
    
    # Fermer l'application
    root.destroy()

# -----------------
# --- Fonctions de navigation et d'affichage ---
# -----------------

def afficher_page(index):
    """Affiche la page correspondant à l'index (0: Beeper, 1: Mode, 2: Menu)."""
    global page_index
    page_index = index
    for f in frames:
        f.pack_forget()
    frames[page_index].pack(pady=10, fill="both", expand=True)

def valider_nom():
    global nom_client
    nom_client = entry_nom.get().strip()
    if nom_client == "":
        messagebox.showwarning("Erreur", "Veuillez entrer un numéro de beeper.")
        return
    # Passage direct à la page 2 (Mode)
    afficher_page(1) 

def choisir_mode(mode):
    global mode_commande
    mode_commande = mode
    lbl_client.config(text=f"Commande de {nom_client} ({mode})")
    # Passage direct à la page 3 (Menu)
    afficher_page(2)

def mettre_a_jour_affichage():
    liste.delete(0, tk.END)
    total_calc = 0.0
    for item in commande:
        liste.insert(tk.END, f"{item['article']} - {item['prix']:.2f}€ | {item['details']}")
        total_calc += item['prix']
    global total
    total = total_calc
    lbl_total.config(text=f"Total : {total:.2f} €")

# -----------------
# --- Fonction principale pour les options ---
# -----------------
def ouvrir_options(article, index=None):
    
    # Si l'article est un sous-menu de SANDWICH, le traiter comme un article simple
    if article in sous_menus_sandwich:
        # L'article principal est "SANDWICH" et le sous-choix est 'article'
        choix_sandwich = article
        article = "SANDWICH"
    else:
        choix_sandwich = None
        
    win = tk.Toplevel(root)
    win.title(f"Options - {article}" if choix_sandwich is None else f"Options - SANDWICH ({choix_sandwich})")
    win.geometry("600x700")
    
    # Variables de contrôle
    nb_var = tk.IntVar(value=0)
    burger_var = tk.StringVar(value="")
    article_var = tk.StringVar(value="")
    kebab_var = tk.StringVar(value="")
    type_kebab_var = tk.StringVar(value="")
    texmex_var = tk.StringVar(value="")
    menu_enfant_var = tk.StringVar(value="")
    simple_var = tk.StringVar(value="")
    sandwich_var = tk.StringVar(value=choix_sandwich if choix_sandwich else "") # Pour SANDWICH
    sauce_var = tk.StringVar(value=sauces_dispo[0]) # Par défaut: "Aucune"
    
    # NOUVELLE VARIABLE POUR L'OPTION MENU +2€
    menu_option_var = tk.BooleanVar(value=False)
    
    # Variables spécifiques pour la BOX
    viande_box_var = tk.StringVar(value="")
    sauce_box_var = tk.StringVar(value="Ketchup") # Sauce par défaut mise à jour
    supp_frites_var = tk.BooleanVar(value=False)
    supp_oignon_var = tk.BooleanVar(value=False)
    
    # NOUVELLES VARIABLES POUR LES SUPPLEMENTS BOX
    supp_viande_var = tk.BooleanVar(value=False)
    supp_fromage_var = tk.BooleanVar(value=False)
    
    main_frame = tk.Frame(win)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    canvas = tk.Canvas(main_frame)
    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)
    
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    tk.Label(scrollable_frame, text=f"{article}", font=("Arial", 20, "bold")).pack(pady=20)

    # --- Pré-remplissage en mode modification ---
    details = ""
    if index is not None:
        item = commande[index]
        details = item['details']
        
        if article == "SANDWICH":
            try:
                # Récupère le nom du sandwich (ex: O'Delice)
                choix_sandwich_mod = item['article'].split("SANDWICH ")[1]
                sandwich_var.set(choix_sandwich_mod)
                sauce_sel = details.split("Sauce: ")[1].split(" |")[0]
                sauce_var.set(sauce_sel)
            except:
                pass
        
        elif article in ["Tacos", "Tacos Gratiné", "Assiette"]:
            try:
                viandes_text = details.split("Viandes: ")[1].split(" |")[0]
                nb_viandes_sel = len(viandes_text.split(", "))
                nb_var.set(nb_viandes_sel)
                sauce_sel = details.split("Sauce: ")[1].split(" |")[0]
                sauce_var.set(sauce_sel)
                # Pré-remplir l'option menu si présente dans les détails
                if "Menu +2€" in details:
                    menu_option_var.set(True)
            except:
                pass 

        elif article == "Burger":
            try:
                burger_var.set(details.split("Taille: ")[1].split(" |")[0])
                sauce_var.set(details.split("Sauce: ")[1].split(" |")[0])
            except:
                pass

        elif article == "BOX":
            try:
                # Extraction des détails de la BOX
                if "Viande:" in details:
                    viande_sel = details.split("Viande: ")[1].split(" |")[0]
                    viande_box_var.set(viande_sel)
                if "Sauce:" in details:
                    sauce_sel = details.split("Sauce: ")[1].split(" |")[0]
                    sauce_box_var.set(sauce_sel)
                if "+ Frites" in details:
                    supp_frites_var.set(True)
                if "+ Oignon" in details:
                    supp_oignon_var.set(True)
                # Pré-remplir les nouveaux suppléments
                if "Suppl. viande +2€" in details:
                    supp_viande_var.set(True)
                if "Suppl. fromage +1€" in details:
                    supp_fromage_var.set(True)
            except:
                pass

        # MODIFICATION : Pré-remplissage pour Tex-Mex
        elif article == "Tex-Mex":
            try:
                choix_texmex = details.split("Choix: ")[1].split(" |")[0]
                texmex_var.set(choix_texmex)
                if "Sauce:" in details:
                    sauce_sel = details.split("Sauce: ")[1].split(" |")[0]
                    sauce_var.set(sauce_sel)
            except:
                pass

    def valider():
        prix_final = 0
        details = ""
        sauce_sel = sauce_var.get()
        
        if article == "SANDWICH":
            choix_sandwich = sandwich_var.get()
            if choix_sandwich == "":
                messagebox.showwarning("Erreur", "Veuillez choisir un sandwich.")
                return
            
            # Gestion des suppléments pour les sandwichs
            supps = []
            suppl_prix = 0
            if 'supp_vars' in locals():
                supps = [s for s, v in supp_vars.items() if v.get()]
                suppl_prix = len(supps) * 1.0 
            
            prix_base = prix_articles[article][choix_sandwich]
            prix_final = prix_base + suppl_prix
            
            details = f"Choix: {choix_sandwich} | Sauce: {sauce_sel}"
            if supps:
                details += f" | Suppléments: {', '.join(supps)} (+{suppl_prix:.2f}€)"
            
            # Nom de l'article affiché dans la liste
            article_nom_final = f"SANDWICH {choix_sandwich}"

        elif article in ["Tacos", "Tacos Gratiné", "Assiette"]:
            nb = nb_var.get()
            if nb == 0:
                messagebox.showwarning("Erreur", f"Veuillez choisir le nombre de viandes.")
                return
            prix_base = prix_articles[article][nb]
            
            viandes_sel = []
            if hasattr(viande_frame, 'selects'):
                viandes_sel = [c.get() for c in viande_frame.selects if c.get()]
            
            if len(viandes_sel) != nb:
                messagebox.showwarning("Erreur", f"Veuillez choisir exactement {nb} viande(s) dans les listes déroulantes.")
                return

            supps = []
            suppl_prix = 0
            if article in ["Tacos", "Tacos Gratiné"] and 'supp_vars' in locals():
                supps = [s for s, v in supp_vars.items() if v.get()]
                suppl_prix = len(supps)
            
            # AJOUT DE L'OPTION MENU +2€
            menu_option = menu_option_var.get()
            if menu_option:
                suppl_prix += 2
                details = f"Viandes: {', '.join(viandes_sel)} | Sauce: {sauce_sel} | Menu +2€"
            else:
                details = f"Viandes: {', '.join(viandes_sel)} | Sauce: {sauce_sel}"
                
            if supps:
                details += f" | Suppléments: {', '.join(supps)} (+{suppl_prix}€)"
            
            prix_final = prix_base + suppl_prix
            article_nom_final = article
            

        elif article == "Burger":
            choix_article = burger_var.get()
            if choix_article == "":
                messagebox.showwarning("Erreur", "Veuillez choisir une taille.")
                return
            prix_base = prix_articles[article][choix_article]
            prix_final = prix_base
            details = f"Taille: {choix_article} | Sauce: {sauce_sel}" 
            article_nom_final = article

        elif article in ["Chicken Burger", "O'Delice Burger"]:
            choix_article = article_var.get()
            if choix_article == "":
                messagebox.showwarning("Erreur", "Veuillez choisir une option.")
                return
            prix_final = prix_articles[article][choix_article]
            details = f"Choix: {choix_article} | Sauce: {sauce_sel}" 
            article_nom_final = article

        elif article == "Kebab":
            choix_article = kebab_var.get()
            type_kebab = type_kebab_var.get()
            if choix_article == "" or type_kebab == "":
                messagebox.showwarning("Erreur", "Veuillez compléter les options.")
                return
            prix_final = prix_articles[article][choix_article]
            details = f"Choix: {choix_article} | Type: {type_kebab} | Sauce: {sauce_sel}" 
            article_nom_final = article

        # MODIFICATION : Gestion du Tex-Mex avec sauce
        elif article == "Tex-Mex":
            choix_texmex = texmex_var.get()
            if choix_texmex == "":
                messagebox.showwarning("Erreur", "Veuillez choisir une option.")
                return
            prix_final = prix_articles[article][choix_texmex]
            details = f"Choix: {choix_texmex} | Sauce: {sauce_sel}"
            article_nom_final = article

        elif article == "Menu Enfant":
            choix_menu_enfant = menu_enfant_var.get()
            if choix_menu_enfant == "":
                messagebox.showwarning("Erreur", "Veuillez choisir une option.")
                return
            prix_final = prix_articles[article][choix_menu_enfant]
            details = f"Choix: {choix_menu_enfant}"
            article_nom_final = article

        elif article in ["Frites", "Dessert", "Boisson"]:
            choix = simple_var.get()
            if choix == "":
                messagebox.showwarning("Erreur", f"Veuillez choisir une option.")
                return
            prix_final = prix_articles[article][choix]
            details = f"Choix: {choix}"
            article_nom_final = article
        
        elif article == "BOX":
            viande_sel = viande_box_var.get()
            sauce_sel = sauce_box_var.get()
            if viande_sel == "":
                messagebox.showwarning("Erreur", "Veuillez choisir une viande pour la BOX.")
                return
            
            prix_final = prix_articles[article]["BOX"]
            details = f"Viande: {viande_sel} | Sauce: {sauce_sel}"
            
            # Gestion des suppléments BOX
            supps = []
            suppl_prix = 0
            
            # NOUVEAUX SUPPLEMENTS
            if supp_viande_var.get():
                supps.append("Suppl. viande +2€")
                suppl_prix += 2
            if supp_fromage_var.get():
                supps.append("Suppl. fromage +1€")
                suppl_prix += 1
            if supp_frites_var.get():
                supps.append("+ Frites")
            if supp_oignon_var.get():
                supps.append("+ Oignon")
            
            if supps:
                details += f" | Suppléments: {', '.join(supps)}"
            
            prix_final += suppl_prix
            article_nom_final = "BOX"
        
        # NOUVEAU CAS POUR SALADE O'DÉLICE
        elif article == "SALADE O'DÉLICE":
            prix_final = prix_articles[article]["SALADE O'DÉLICE"]
            details = f"Choix: Salade O'Délice | Sauce: {sauce_sel}"
            article_nom_final = "SALADE O'DÉLICE"
        
        else:
             # Cas où le sous-menu de SANDWICH est cliqué directement
            if article in sous_menus_sandwich:
                 prix_final = prix_articles["SANDWICH"][article]
                 details = f"Choix: {article} | Sauce: {sauce_sel}"
                 article_nom_final = f"SANDWICH {article}"

        item = {"article": article_nom_final, "prix": prix_final, "details": details}
        
        if index is not None:
            commande[index] = item 
        else:
            commande.append(item)
            
        mettre_a_jour_affichage()
        win.destroy()

    btn_valider = creer_bouton_tactile(scrollable_frame, "VALIDER", valider, bg="#27ae60", fg="white", height=2)
    btn_valider.pack(pady=20)
    
    # --- Options pour les différents articles ---

    if article == "SANDWICH":
        tk.Label(scrollable_frame, text="Choix du sandwich :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
        
        # Le choix est déjà présélectionné si l'on vient du menu principal
        for choix, prix in prix_articles["SANDWICH"].items():
            btn = tk.Radiobutton(scrollable_frame, text=f"{choix} - {prix}€",
                                 variable=sandwich_var, value=choix, font=("Arial", 14),
                                 indicatoron=1, width=25, height=2)
            btn.pack(anchor="w", padx=20, pady=5)
            
        
        # Suppléments (Optionnel pour les sandwichs)
        tk.Label(scrollable_frame, text="Suppléments (+1€ chacun) :", font=("Arial", 14)).pack(anchor="w", padx=10, pady=10)
        supp_vars = {}
        # Pré-remplissage des suppléments en mode modification
        supps_actuels = []
        if index is not None and "Suppléments: " in details:
             supps_actuels = details.split("Suppléments: ")[1].split(" (")[0].split(", ")
             
        for s in supplements_dispo:
            var = tk.BooleanVar()
            if s in supps_actuels: 
                var.set(True)
            cb = tk.Checkbutton(scrollable_frame, text=s, variable=var, font=("Arial", 12),
                                height=2, width=20, anchor="w")
            cb.pack(anchor="w", padx=20, pady=3)
            supp_vars[s] = var
            
        # Sauce
        tk.Label(scrollable_frame, text="Sauce :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
        sauce_combo = ttk.Combobox(scrollable_frame, values=sauces_dispo, state="readonly",
                                   font=("Arial", 14), height=10, textvariable=sauce_var)
        if index is not None and "Sauce: " in details:
             sauce_var.set(details.split("Sauce: ")[1].split(" |")[0])
        elif sauce_var.get() not in sauces_dispo:
             sauce_combo.current(0) 
        sauce_combo.pack(fill="x", padx=20, pady=8)

    # NOUVEAU CAS POUR SALADE O'DÉLICE
    elif article == "SALADE O'DÉLICE":
        tk.Label(scrollable_frame, text="SALADE O'DÉLICE - 7.00€", font=("Arial", 18, "bold"), fg="#2ecc71").pack(pady=10)
        
        tk.Label(scrollable_frame, text="Composition :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
        tk.Label(scrollable_frame, text="• Salade verte\n• Tenders\n• Fromage\n• Emmental\n• Oignon", 
                 font=("Arial", 14), justify="left").pack(anchor="w", padx=20, pady=5)
        
        # Sauce pour la salade
        tk.Label(scrollable_frame, text="Sauce :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
        sauce_combo = ttk.Combobox(scrollable_frame, values=sauces_dispo, state="readonly",
                                   font=("Arial", 14), height=10, textvariable=sauce_var)
        if index is not None and "Sauce: " in details:
             sauce_var.set(details.split("Sauce: ")[1].split(" |")[0])
        elif sauce_var.get() not in sauces_dispo:
             sauce_combo.current(0) 
        sauce_combo.pack(fill="x", padx=20, pady=8)

    elif article in ["Tacos", "Tacos Gratiné", "Assiette"]:
        tk.Label(scrollable_frame, text="Nombre de viandes :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
        for nb, prix in prix_articles[article].items():
            btn = tk.Radiobutton(scrollable_frame, text=f"{nb} viande(s) - {prix}€",
                                 variable=nb_var, value=nb, font=("Arial", 14),
                                 indicatoron=1, width=25, height=2)
            btn.pack(anchor="w", padx=20, pady=5)

        # NOUVELLE OPTION : MENU +2€ (uniquement pour Tacos et Tacos Gratiné)
        if article in ["Tacos", "Tacos Gratiné"]:
            tk.Label(scrollable_frame, text="Options Menu :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
            cb_menu = tk.Checkbutton(scrollable_frame, text="Menu +2€ (Frites + Boisson)", 
                                    variable=menu_option_var, font=("Arial", 14),
                                    height=2, width=30, anchor="w")
            cb_menu.pack(anchor="w", padx=20, pady=5)

        viande_frame = tk.Frame(scrollable_frame)
        viande_frame.pack(pady=10, fill="x")

        def maj_viandes(*args):
            viandes_a_pre_remplir = []
            if index is not None and nb_var.get() > 0:
                try:
                    viandes_text = details.split("Viandes: ")[1].split(" |")[0]
                    viandes_a_pre_remplir = viandes_text.split(", ")
                    viandes_a_pre_remplir = viandes_a_pre_remplir[:nb_var.get()] 
                except:
                    pass

            for widget in viande_frame.winfo_children():
                widget.destroy()
            nb = nb_var.get()
            if nb > 0:
                tk.Label(viande_frame, text="Choisissez vos viandes :", font=("Arial", 14)).pack(anchor="w")
                selects = []
                for i in range(nb):
                    combo = ttk.Combobox(viande_frame, values=viandes_dispo, state="readonly", font=("Arial", 14), height=15)
                    
                    if i < len(viandes_a_pre_remplir) and viandes_a_pre_remplir[i] in viandes_dispo:
                        combo.set(viandes_a_pre_remplir[i])
                    else:
                        combo.current(0)
                        
                    combo.pack(fill="x", padx=20, pady=8)
                    selects.append(combo)
                viande_frame.selects = selects
            
            scrollable_frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

        nb_var.trace("w", maj_viandes)
        
        if index is not None and nb_var.get() > 0:
            maj_viandes() 
        elif index is None:
            nb_var.set(1) 

        if article in ["Tacos", "Tacos Gratiné"]:
            tk.Label(scrollable_frame, text="Suppléments (+1€ chacun) :", font=("Arial", 14)).pack(anchor="w", padx=10, pady=10)
            supp_vars = {}
            for s in supplements_dispo:
                var = tk.BooleanVar()
                if index is not None and s in details: 
                    var.set(True)
                cb = tk.Checkbutton(scrollable_frame, text=s, variable=var, font=("Arial", 12),
                                     height=2, width=20, anchor="w")
                cb.pack(anchor="w", padx=20, pady=3)
                supp_vars[s] = var
        
        tk.Label(scrollable_frame, text="Sauce :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
        sauce_combo = ttk.Combobox(scrollable_frame, values=sauces_dispo, state="readonly",
                                   font=("Arial", 14), height=10, textvariable=sauce_var)
        if index is not None and "Sauce: " in details:
             sauce_var.set(details.split("Sauce: ")[1].split(" |")[0])
        elif sauce_var.get() not in sauces_dispo:
             sauce_combo.current(0) 
        sauce_combo.pack(fill="x", padx=20, pady=8)

    elif article in ["Burger", "Chicken Burger", "O'Delice Burger", "Kebab"]:
        
        if article == "Burger":
            tk.Label(scrollable_frame, text="Taille du burger :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
            for taille, prix in prix_articles[article].items():
                btn = tk.Radiobutton(scrollable_frame, text=f"{taille} - {prix}€",
                                     variable=burger_var, value=taille, font=("Arial", 14),
                                     indicatoron=1, width=20, height=2)
                btn.pack(anchor="w", padx=20, pady=5)
                if index is not None and taille in details:
                    burger_var.set(taille)

        elif article in ["Chicken Burger", "O'Delice Burger"]:
            tk.Label(scrollable_frame, text="Choix :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
            for choix, prix in prix_articles[article].items():
                btn = tk.Radiobutton(scrollable_frame, text=f"{choix} - {prix}€",
                                     variable=article_var, value=choix, font=("Arial", 14),
                                     indicatoron=1, width=20, height=2)
                btn.pack(anchor="w", padx=20, pady=5)
                if index is not None and choix in details:
                    article_var.set(choix)

        elif article == "Kebab":
            tk.Label(scrollable_frame, text="Choix :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
            for choix, prix in prix_articles[article].items():
                btn = tk.Radiobutton(scrollable_frame, text=f"{choix} - {prix}€",
                                     variable=kebab_var, value=choix, font=("Arial", 14),
                                     indicatoron=1, width=20, height=2)
                btn.pack(anchor="w", padx=20, pady=5)
                if index is not None and choix in details:
                    kebab_var.set(choix)

            tk.Label(scrollable_frame, text="Type :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
            tk.Radiobutton(scrollable_frame, text="Pain", variable=type_kebab_var, 
                           value="Pain", font=("Arial", 14), indicatoron=1, width=15, height=2).pack(anchor="w", padx=20, pady=5)
            tk.Radiobutton(scrollable_frame, text="Galette", variable=type_kebab_var, 
                           value="Galette", font=("Arial", 14), indicatoron=1, width=15, height=2).pack(anchor="w", padx=20, pady=5)
            if index is not None:
                if "Pain" in details:
                    type_kebab_var.set("Pain")
                elif "Galette" in details:
                    type_kebab_var.set("Galette")
        
        tk.Label(scrollable_frame, text="Sauce :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
        sauce_combo = ttk.Combobox(scrollable_frame, values=sauces_dispo, state="readonly",
                                   font=("Arial", 14), height=10, textvariable=sauce_var)
        if index is not None and "Sauce: " in details:
             sauce_var.set(details.split("Sauce: ")[1].split(" |")[0])
        elif sauce_var.get() not in sauces_dispo:
             sauce_combo.current(0) 
        sauce_combo.pack(fill="x", padx=20, pady=8)

    elif article == "BOX":
        # Options spécifiques pour la BOX
        tk.Label(scrollable_frame, text="BOX - 7.50€", font=("Arial", 18, "bold"), fg="#e74c3c").pack(pady=10)
        
        # Sélection de la viande
        tk.Label(scrollable_frame, text="Choisissez votre viande :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
        for viande in viandes_box:
            btn = tk.Radiobutton(scrollable_frame, text=viande,
                                 variable=viande_box_var, value=viande, font=("Arial", 14),
                                 indicatoron=1, width=20, height=2)
            btn.pack(anchor="w", padx=20, pady=5)
            if index is not None and viande in details:
                viande_box_var.set(viande)
        
        # Sélection de la sauce
        tk.Label(scrollable_frame, text="Choisissez votre sauce :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
        sauce_combo = ttk.Combobox(scrollable_frame, values=sauces_box, state="readonly",
                                   font=("Arial", 14), height=10, textvariable=sauce_box_var)
        if index is not None and "Sauce: " in details:
            sauce_sel = details.split("Sauce: ")[1].split(" |")[0]
            sauce_box_var.set(sauce_sel)
        else:
            sauce_combo.current(0)  # Ketchup par défaut
        sauce_combo.pack(fill="x", padx=20, pady=8)
        
        # NOUVEAUX SUPPLEMENTS BOX
        tk.Label(scrollable_frame, text="Suppléments payants :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
        
        cb_viande = tk.Checkbutton(scrollable_frame, text="Suppl. viande +2€", variable=supp_viande_var, 
                                  font=("Arial", 14), height=2, width=20, anchor="w")
        cb_viande.pack(anchor="w", padx=20, pady=5)
        
        cb_fromage = tk.Checkbutton(scrollable_frame, text="Suppl. fromage +1€", variable=supp_fromage_var, 
                                   font=("Arial", 14), height=2, width=20, anchor="w")
        cb_fromage.pack(anchor="w", padx=20, pady=5)
        
        # Suppléments gratuits existants
        tk.Label(scrollable_frame, text="Suppléments gratuits :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
        
        cb_frites = tk.Checkbutton(scrollable_frame, text="+ Frites", variable=supp_frites_var, 
                                  font=("Arial", 14), height=2, width=20, anchor="w")
        cb_frites.pack(anchor="w", padx=20, pady=5)
        
        cb_oignon = tk.Checkbutton(scrollable_frame, text="+ Oignon", variable=supp_oignon_var, 
                                  font=("Arial", 14), height=2, width=20, anchor="w")
        cb_oignon.pack(anchor="w", padx=20, pady=5)

    # MODIFICATION : Ajout des sauces pour Tex-Mex
    elif article == "Tex-Mex":
        tk.Label(scrollable_frame, text="Choix :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
        
        for choix, prix in prix_articles[article].items():
            btn = tk.Radiobutton(scrollable_frame, text=f"{choix} - {prix}€",
                                 variable=texmex_var, value=choix, font=("Arial", 14),
                                 indicatoron=1, width=30, height=2)
            btn.pack(anchor="w", padx=20, pady=5)
            if index is not None and choix in details:
                texmex_var.set(choix)
        
        # AJOUT : Sélection de sauce pour Tex-Mex
        tk.Label(scrollable_frame, text="Sauce :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
        sauce_combo = ttk.Combobox(scrollable_frame, values=sauces_dispo, state="readonly",
                                   font=("Arial", 14), height=10, textvariable=sauce_var)
        if index is not None and "Sauce: " in details:
            sauce_sel = details.split("Sauce: ")[1].split(" |")[0]
            sauce_var.set(sauce_sel)
        elif sauce_var.get() not in sauces_dispo:
            sauce_combo.current(0)
        sauce_combo.pack(fill="x", padx=20, pady=8)

    elif article in ["Menu Enfant", "Frites", "Dessert", "Boisson"]:
        
        var_to_use = None
        if article == "Menu Enfant":
             var_to_use = menu_enfant_var
        elif article in ["Frites", "Dessert", "Boisson"]:
             var_to_use = simple_var

        tk.Label(scrollable_frame, text="Choix :", font=("Arial", 16)).pack(anchor="w", padx=10, pady=10)
        
        for choix, prix in prix_articles[article].items():
            btn = tk.Radiobutton(scrollable_frame, text=f"{choix} - {prix}€",
                                 variable=var_to_use, value=choix, font=("Arial", 14),
                                 indicatoron=1, width=30, height=2)
            btn.pack(anchor="w", padx=20, pady=5)
            if index is not None and choix in details:
                var_to_use.set(choix)

# --- Fonctions Modifier/Supprimer ---
def supprimer_article():
    selection = liste.curselection()
    if not selection:
        messagebox.showwarning("Erreur", "Sélectionnez un article à supprimer.")
        return
    index = selection[0]
    del commande[index]
    mettre_a_jour_affichage()

def modifier_article():
    selection = liste.curselection()
    if not selection:
        messagebox.showwarning("Erreur", "Sélectionnez un article à modifier.")
        return
    index = selection[0]
    # L'article principal est stocké dans l'objet 'commande', on utilise celui-ci
    article_complet = commande[index]["article"] 
    # Extraire la catégorie principale (Tacos, Burger, SANDWICH, etc.)
    if article_complet.startswith("SANDWICH"):
        article_type = "SANDWICH"
    else:
        # Tente de trouver la clé principale dans prix_articles (ex: Tacos, Burger)
        for key in prix_articles.keys():
            if key in article_complet:
                article_type = key
                break
        else:
             messagebox.showerror("Erreur", "Type d'article non reconnu pour la modification.")
             return
             
    ouvrir_options(article_type, index) 

# -----------------
# --- Interface principale ---
# -----------------
root = tk.Tk()
# Mise à jour du titre
root.title(f"{NOM_ENTREPRISE} - Interface Tactile")
root.geometry("1200x900")
root.config(bg="#f4f4f4")

init_db()

# La liste des frames de pages
frames = []

# === NOUVELLE DISPOSITION : BOUTONS VERTICAUX À GAUCHE ET À DROITE ===

# --- BARRE LATÉRALE GAUCHE ---
left_sidebar = tk.Frame(root, bg="#34495e", width=200)
left_sidebar.pack(side="left", fill="y", padx=2, pady=2)
left_sidebar.pack_propagate(False)

# --- BOUTONS VERTICAUX GAUCHE ---
creer_bouton_tactile(left_sidebar, "🆕 NOUVELLE COMMANDE", nouvelle_commande,
                     bg="#e74c3c", fg="white", font=("Arial", 12, "bold"), height=2, width=15).pack(pady=10, padx=5, fill="x")

creer_bouton_tactile(left_sidebar, "💾 SAUVEGARDER", sauvegarder_commande,
                     bg="#9b59b6", fg="white", font=("Arial", 12, "bold"), height=2, width=15).pack(pady=10, padx=5, fill="x")

creer_bouton_tactile(left_sidebar, "🔍 RECHERCHER", rechercher_commandes,
                     bg="#f39c12", fg="white", font=("Arial", 12, "bold"), height=2, width=15).pack(pady=10, padx=5, fill="x")

# --- BARRE LATÉRALE DROITE ---
right_sidebar = tk.Frame(root, bg="#2c3e50", width=200)
right_sidebar.pack(side="right", fill="y", padx=2, pady=2)
right_sidebar.pack_propagate(False)

# --- BOUTONS VERTICAUX DROITE ---
creer_bouton_tactile(right_sidebar, "📊 STATISTIQUES", afficher_statistiques,
                     bg="#8e44ad", fg="white", font=("Arial", 12, "bold"), height=2, width=15).pack(pady=10, padx=5, fill="x")

creer_bouton_tactile(right_sidebar, "⚙️ OPTIONS", afficher_options,
                     bg="#34495e", fg="white", font=("Arial", 12, "bold"), height=2, width=15).pack(pady=10, padx=5, fill="x")

creer_bouton_tactile(right_sidebar, "🚪 QUITTER", quitter_application,
                     bg="#c0392b", fg="white", font=("Arial", 12, "bold"), height=2, width=15).pack(pady=10, padx=5, fill="x")

# --- BARRE DU HAUT POUR LES AUTRES BOUTONS ---
top_action_frame = tk.Frame(root, bg="#2c3e50", height=80)
top_action_frame.pack(fill="x", pady=2)
top_action_frame.pack_propagate(False)

# --- BOUTONS EN HAUT AU CENTRE ---
center_frame = tk.Frame(top_action_frame, bg="#2c3e50")
center_frame.pack(expand=True, pady=10)

creer_bouton_tactile(center_frame, "🖨️ IMPRIMER", traiter_impression_sauvegarde,
                     bg="#16a085", fg="white", **ACTION_BUTTON_STYLE).pack(side="left", padx=5)

creer_bouton_tactile(center_frame, "📄 AFFICHER TICKET", afficher_ticket_client,
                     bg="#f1c40f", fg="black", **ACTION_BUTTON_STYLE).pack(side="left", padx=5)

# En-tête avec date et heure au centre
header_frame = tk.Frame(root, bg="#2c3e50", height=60)
header_frame.pack(fill="x", pady=2)
header_frame.pack_propagate(False)

# Affichage du nom de l'entreprise
tk.Label(header_frame, text=NOM_ENTREPRISE, font=("Arial", 24, "bold"), fg="white", bg="#2c3e50").pack(side="left", padx=20)

lbl_date_heure = tk.Label(header_frame, text="", font=("Arial", 12), fg="#f1c40f", bg="#2c3e50")
lbl_date_heure.pack(side="right", padx=20)
mettre_a_jour_heure()

# === PAGE 1: NUMÉRO DE BEEPER ===
page_nom = tk.Frame(root, bg="#f4f4f4")
frames.append(page_nom)

tk.Label(page_nom, text="1. Entrez le numéro de beeper :", font=("Arial", 28, "bold"), bg="#f4f4f4").pack(pady=50)

entry_nom = tk.Entry(page_nom, font=("Arial", 24), width=30)
entry_nom.pack(pady=20)

creer_bouton_tactile(page_nom, "VALIDER BEEPER", valider_nom, bg="#3498db", fg="white", height=2).pack(pady=40)

# === PAGE 2: MODE DE COMMANDE ===
page_mode = tk.Frame(root, bg="#f4f4f4")
frames.append(page_mode)

tk.Label(page_mode, text="2. Choisissez le mode de commande :", font=("Arial", 28, "bold"), bg="#f4f4f4").pack(pady=50)

mode_frame = tk.Frame(page_mode)
mode_frame.pack(pady=20)

creer_bouton_tactile(mode_frame, "SUR PLACE", lambda: choisir_mode("Sur place"), 
                     bg="#2ecc71", fg="white", width=25).pack(side="left", padx=20)
creer_bouton_tactile(mode_frame, "À EMPORTER", lambda: choisir_mode("À emporter"), 
                     bg="#e67e22", fg="white", width=25).pack(side="left", padx=20)

# === PAGE 3: MENU PRINCIPAL & COMMANDE ===
page_menu = tk.Frame(root, bg="#f4f4f4")
frames.append(page_menu)

# --- Affichage Beeper/Mode ---
lbl_client = tk.Label(page_menu, text="", font=("Arial", 18, "bold"), bg="#f4f4f4")
lbl_client.pack(pady=10)

# --- Zone Menu et Commande ---
main_content_frame = tk.Frame(page_menu, bg="#f4f4f4")
main_content_frame.pack(fill="both", expand=True)

# Cadre du Menu (Gauche)
menu_frame = tk.Frame(main_content_frame, bg="#f4f4f4", padx=10, pady=10)
menu_frame.pack(side="left", fill="both", expand=True)

# Cadre de la Commande (Droite)
commande_frame = tk.Frame(main_content_frame, bg="#f4f4f4", padx=10, pady=10)
commande_frame.pack(side="right", fill="both", expand=True, ipadx=10)

# --- Menu Principal ---
menu_grid_frame = tk.Frame(menu_frame)
menu_grid_frame.pack(pady=10)

# Liste des catégories pour le menu principal
articles_menu_page_3 = [
    "TACOS", "BURGER", "Kebab",  
    "Assiette", "Tex-Mex", "Menu Enfant", 
    "SANDWICH", "BOX", "SALADE O'DÉLICE", "Frites", "Dessert", "Boisson"
]

# Fonction de création de boutons du menu
def creer_boutons_menu():
    row, col = 0, 0
    # On ajoute des espaces vides pour avoir 3 colonnes par défaut
    for i in range(3):
        menu_grid_frame.grid_columnconfigure(i, weight=1) 
        
    for item in articles_menu_page_3:
        if item == "SANDWICH":
            # Le bouton SANDWICH doit afficher ses sous-menus au lieu d'ouvrir les options
            btn_commande = lambda s=item: creer_sous_menu(s)
        elif item == "BURGER":
            # Le bouton BURGER doit afficher les types de burgers
            btn_commande = lambda s=item: creer_sous_menu_burger(s)
        elif item == "TACOS":
            # Le bouton TACOS doit afficher les types de tacos
            btn_commande = lambda s=item: creer_sous_menu_tacos(s)
        elif item in prix_articles:
            # Les autres boutons ouvrent directement la fenêtre d'options
            btn_commande = lambda a=item: ouvrir_options(a)
        else:
            btn_commande = lambda: None

        # Couleur différente pour les salades (vert)
        bg_color = "#2ecc71" if item == "SALADE O'DÉLICE" else "#e67e22"
        
        btn = creer_bouton_tactile(menu_grid_frame, item, btn_commande, 
                                   bg=bg_color, fg="white", font=("Arial", 16, "bold"), height=3, width=15)
        btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        col += 1
        if col > 2:
            col = 0
            row += 1

creer_boutons_menu()

# --- Fonction pour afficher le sous-menu SANDWICH ---
def creer_sous_menu(categorie):
    if categorie == "SANDWICH":
        # Masquer la grille du menu principal
        menu_grid_frame.pack_forget()
        
        # Vider et afficher la grille du sous-menu
        for widget in sous_menu_frame.winfo_children():
            widget.destroy()
            
        sous_menu_frame.pack(pady=10, fill="both", expand=True)
        
        row, col = 0, 0
        for i in range(3):
            sous_menu_frame.grid_columnconfigure(i, weight=1) 
        
        # Bouton de retour
        btn_retour = creer_bouton_tactile(sous_menu_frame, "◀️ Retour au Menu", 
                                         lambda: [sous_menu_frame.pack_forget(), menu_grid_frame.pack(pady=10)], 
                                         bg="#34495e", fg="white", font=("Arial", 16, "bold"), height=2, width=15)
        btn_retour.grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        row += 1
        
        for sub_item in sous_menus_sandwich:
            # Chaque sous-menu ouvre la fenêtre d'options (gestion sauce/suppléments)
            btn = creer_bouton_tactile(sous_menu_frame, sub_item, 
                                       lambda a=sub_item: ouvrir_options(a), 
                                       bg="#3498db", fg="white", font=("Arial", 16, "bold"), height=3, width=15)
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            col += 1
            if col > 2:
                col = 0
                row += 1

# --- Fonction pour afficher le sous-menu BURGER ---
def creer_sous_menu_burger(categorie):
    if categorie == "BURGER":
        # Masquer la grille du menu principal
        menu_grid_frame.pack_forget()
        
        # Vider et afficher la grille du sous-menu burger
        for widget in sous_menu_burger_frame.winfo_children():
            widget.destroy()
            
        sous_menu_burger_frame.pack(pady=10, fill="both", expand=True)
        
        row, col = 0, 0
        for i in range(3):
            sous_menu_burger_frame.grid_columnconfigure(i, weight=1) 
        
        # Bouton de retour
        btn_retour = creer_bouton_tactile(sous_menu_burger_frame, "◀️ Retour au Menu", 
                                         lambda: [sous_menu_burger_frame.pack_forget(), menu_grid_frame.pack(pady=10)], 
                                         bg="#34495e", fg="white", font=("Arial", 16, "bold"), height=2, width=15)
        btn_retour.grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        row += 1
        
        for sub_item in sous_menus_burger:
            # Chaque type de burger ouvre la fenêtre d'options correspondante
            btn = creer_bouton_tactile(sous_menu_burger_frame, sub_item, 
                                       lambda a=sub_item: ouvrir_options(a), 
                                       bg="#e67e22", fg="white", font=("Arial", 16, "bold"), height=3, width=15)
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            col += 1
            if col > 2:
                col = 0
                row += 1

# --- Fonction pour afficher le sous-menu TACOS ---
def creer_sous_menu_tacos(categorie):
    if categorie == "TACOS":
        # Masquer la grille du menu principal
        menu_grid_frame.pack_forget()
        
        # Vider et afficher la grille du sous-menu tacos
        for widget in sous_menu_tacos_frame.winfo_children():
            widget.destroy()
            
        sous_menu_tacos_frame.pack(pady=10, fill="both", expand=True)
        
        row, col = 0, 0
        for i in range(3):
            sous_menu_tacos_frame.grid_columnconfigure(i, weight=1) 
        
        # Bouton de retour
        btn_retour = creer_bouton_tactile(sous_menu_tacos_frame, "◀️ Retour au Menu", 
                                         lambda: [sous_menu_tacos_frame.pack_forget(), menu_grid_frame.pack(pady=10)], 
                                         bg="#34495e", fg="white", font=("Arial", 16, "bold"), height=2, width=15)
        btn_retour.grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        row += 1
        
        for sub_item in sous_menus_tacos:
            # Chaque type de tacos ouvre la fenêtre d'options correspondante
            btn = creer_bouton_tactile(sous_menu_tacos_frame, sub_item, 
                                       lambda a=sub_item: ouvrir_options(a), 
                                       bg="#e67e22", fg="white", font=("Arial", 16, "bold"), height=3, width=15)
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            col += 1
            if col > 2:
                col = 0
                row += 1

# Cadre pour le sous-menu SANDWICH (initialement masqué)
sous_menu_frame = tk.Frame(menu_frame, bg="#f4f4f4")

# Cadre pour le sous-menu BURGER (initialement masqué)
sous_menu_burger_frame = tk.Frame(menu_frame, bg="#f4f4f4")

# Cadre pour le sous-menu TACOS (initialement masqué)
sous_menu_tacos_frame = tk.Frame(menu_frame, bg="#f4f4f4")

# --- Liste de Commande (Droite) ---
tk.Label(commande_frame, text="📋 COMMANDE :", font=("Arial", 18, "bold"), bg="#f4f4f4").pack(pady=10)

# Liste des articles
liste = tk.Listbox(commande_frame, font=("Arial", 12), height=20, width=60, selectmode=tk.SINGLE)
liste.pack(fill="both", expand=True)

# Barre de défilement pour la liste
scrollbar = tk.Scrollbar(liste, orient=tk.VERTICAL)
liste.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=liste.yview)

# --- Boutons Modifier / Supprimer ---
btn_mod_sup_frame = tk.Frame(commande_frame, bg="#f4f4f4")
btn_mod_sup_frame.pack(fill="x", pady=10)

creer_bouton_tactile(btn_mod_sup_frame, "✏️ MODIFIER", modifier_article, 
                     bg="#3498db", fg="white", font=("Arial", 12, "bold"), height=2, width=15).pack(side="left", fill="x", expand=True, padx=5)
                     
creer_bouton_tactile(btn_mod_sup_frame, "🗑️ SUPPRIMER", supprimer_article, 
                     bg="#e74c3c", fg="white", font=("Arial", 12, "bold"), height=2, width=15).pack(side="left", fill="x", expand=True, padx=5)

# --- Affichage Total ---
lbl_total = tk.Label(commande_frame, text="Total : 0 €", font=("Arial", 32, "bold"), fg="#e74c3c", bg="#f4f4f4")
lbl_total.pack(pady=10)

# Afficher la première page au lancement
afficher_page(0)

root.mainloop()