import streamlit as st
import tempfile
from stl import mesh
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from streamlit_stl import stl_from_file

# Configuration de la page
st.set_page_config(page_title="IDPAN3D - Portail Client", page_icon="⚙️", layout="wide")

# ==========================================
# 🎨 LE PACK DESIGN IDPAN3D (CSS FORCE)
# ==========================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Lobster&display=swap');

        .stApp { background-color: #111111; color: #ffffff; }

        h1, h2, h3 { 
            font-family: 'Lobster', cursive !important; 
            color: #FFCC00 !important; 
            letter-spacing: 1px;
            font-weight: normal;
        }

        .stButton>button { 
            background-color: #FFCC00; 
            color: #111111; 
            font-weight: bold; 
            width: 100%; 
            border: none; 
            text-transform: uppercase;
            transition: all 0.3s ease;
        }
        .stButton>button:hover { background-color: #ffffff; color: #111111; }

        .price-box { 
            background-color: #FFCC00; 
            color: #111111; 
            padding: 20px; 
            border-radius: 8px; 
            text-align: center; 
            box-shadow: 0 4px 15px rgba(255,204,0,0.2);
        }
        
        .price-box h1, .price-box h3 {
            font-family: 'Arial', sans-serif !important;
            color: #111111 !important;
            margin: 0;
        }

        .stTextInput input, .stNumberInput input {
            background-color: #222222 !important;
            color: #ffffff !important;
            border: 1px solid #444444 !important;
        }
        div[data-baseweb="select"] > div {
            background-color: #222222 !important;
            color: #ffffff !important;
            border: 1px solid #444444 !important;
        }
        
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🚀 LE CONTENU DE L'APPLICATION
# ==========================================

st.markdown("<h1 style='text-align: center; font-size: 4rem; color: #FFCC00;'>IDPAN3D</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888; text-transform: uppercase; letter-spacing: 2px;'>Portail Client · Devis & Production</p>", unsafe_allow_html=True)
st.divider()

col_left, col_right = st.columns(2, gap="large")

# ----------------- COLONNE GAUCHE (TECHNIQUE & 3D) -----------------
with col_left:
    st.subheader("1. Fichier 3D")
    uploaded_file = st.file_uploader("Glissez votre fichier .STL ici", type=['stl'])
    
    st.markdown("""
        <p style='font-size: 12px; color: #aaa; font-style: italic; margin-top: -10px; margin-bottom: 20px;'>
            🔒 <b>Confidentialité garantie :</b> Les fichiers STL envoyés sont traités en toute confidentialité, 
            dans le strict respect de vos droits et de la propriété intellectuelle.
        </p>
    """, unsafe_allow_html=True)
    
    volume_cm3 = 0
    dim_x = dim_y = dim_z = 0
    is_printable = False  
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.stl') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
            
        try:
            stl_mesh = mesh.Mesh.from_file(tmp_path)
            volume_mm3 = stl_mesh.get_mass_properties()[0]
            volume_cm3_calc = float(volume_mm3 / 1000.0)
            minx, maxx = stl_mesh.x.min(), stl_mesh.x.max()
            miny, maxy = stl_mesh.y.min(), stl_mesh.y.max()
            minz, maxz = stl_mesh.z.min(), stl_mesh.z.max()
            dim_x, dim_y, dim_z = float(maxx - minx), float(maxy - miny), float(maxz - minz)
            
            # Limites Prusa Core One + : 250 x 220 x 270 mm
            machine_limits = sorted([250.0, 220.0, 270.0])
            part_dims = sorted([dim_x, dim_y, dim_z])
            
            if part_dims[0] > machine_limits[0] or part_dims[1] > machine_limits[1] or part_dims[2] > machine_limits[2]:
                st.error("⚠️ **HORS DIMENSIONS** : Ce fichier dépasse la capacité de notre plus grande machine. Veuillez nous contacter directement au **06 78 22 57 76** pour une étude de découpe ou d'assemblage sur-mesure.")
                volume_cm3 = 0 
            else:
                is_printable = True
                volume_cm3 = volume_cm3_calc
                st.success(f"✅ Analyse réussie : {uploaded_file.name}")
                st.info(f"**Dimensions :** {dim_x:.2f} x {dim_y:.2f} x {dim_z:.2f} mm\n\n**Volume matière :** {volume_cm3:.2f} cm³")
            
            st.write("🔍 **Aperçu interactif :**")
            stl_from_file(
                file_path=tmp_path, 
                color='#FFCC00',        
                material='material',    
                auto_rotate=True,       
                height=300              
            )
            
        except Exception as e:
            st.error(f"Erreur de lecture du fichier STL : {e}")

    st.write("") 
    
    st.subheader("2. Cahier des Charges")
    
    mat_dict = {
        "🟢 STANDARD - Décoration / Maquette (PLA)": 0.15,
        "🟢 STANDARD - Mécanique / Étanchéité (PETG)": 0.18,
        "🟠 TECHNIQUE - Pièce mécanique / Chaleur (ABS)": 0.20,
        "🟠 TECHNIQUE - Extérieur / Résistance UV (ASA)": 0.25,
        "🔵 SPÉCIAL - Pièce souple / Amortisseur (TPU)": 0.35,
        "⚫ EXTRÊME - Aspect Mat premium / Rigide (PLA-CF)": 0.25,
        "⚫ EXTRÊME - Haute rigidité industrielle (PETG-CF)": 0.30,
        "⚫ EXTRÊME - Pièce Automobile / Haute Temp (ABS-CF)": 0.40
    }
    
    qual_dict = {
        "⚡ Rapide (0.28mm - Prototypes)": 1.0,
        "📐 Standard (0.20mm - Industriel)": 1.2,
        "🔍 Haute Fidélité (0.12mm - Précision)": 1.5
    }
    
    mat_choice = st.selectbox("Usage de la pièce (Matière)", list(mat_dict.keys()))
    
    col2a, col2b = st.columns([2, 1])
    with col2a:
        qual_choice = st.selectbox("Qualité de finition", list(qual_dict.keys()))
    with col2b:
        qty = st.number_input("Quantité", min_value=1, value=1)


# ----------------- COLONNE DROITE (OPTIONS & LOGISTIQUE) -----------------
with col_right:
    st.subheader("3. Configuration de la commande")
    
    # Choix livraison
    fdp_dict = {
        "📦 Retrait à l'atelier (Gratuit)": 0.00,
        "🚚 Livraison Standard (Colissimo/Mondial Relay)": 6.90,
        "⚡ Livraison Express (Chronopost 24h)": 12.90
    }
    fdp_choice = st.selectbox("Sélectionnez votre mode de retrait", list(fdp_dict.keys()))
    
    # IDÉE 1 : Option Coupe-File (Urgence)
    urgency_option = st.checkbox("🚀 **Option Coupe-File** : Production prioritaire, départ de l'atelier sous 24h (+30%)")
    
    # IDÉE 4 : Code Promo
    promo_code = st.text_input("🎟️ Code promotionnel (Optionnel)").strip().upper()
    
    # --- CALCUL DYNAMIQUE DU PRIX (INCLUT LES IDÉES 1, 2, 4) ---
    final_price = 0.0
    discount_text = ""
    
    if is_printable and volume_cm3 > 0:
        base_price = 15 + (volume_cm3 * mat_dict[mat_choice] * qual_dict[qual_choice])
        total_pieces = base_price * qty
        
        # IDÉE 2 : Tarifs dégressifs automatiques
        if qty >= 50:
            total_pieces *= 0.80  # -20%
            discount_text += "🎉 Remise de volume -20% appliquée ! "
        elif qty >= 10:
            total_pieces *= 0.90  # -10%
            discount_text += "🎉 Remise de volume -10% appliquée ! "
            
        # Application de l'Idée 4 (Codes promo)
        if promo_code == "BIENVENUE10":
            total_pieces *= 0.90
            discount_text += "🎟️ Code BIENVENUE10 actif (-10%) ! "
        elif promo_code == "LINKEDIN2026":
            total_pieces *= 0.80
            discount_text += "🎟️ Code LINKEDIN2026 actif (-20%) ! "
        elif promo_code != "":
            st.caption("❌ Code promo inconnu.")
            
        # Application de l'Idée 1 (Coupe-file)
        if urgency_option:
            total_pieces *= 1.30
            
        final_price = total_pieces + fdp_dict[fdp_choice]

    st.write("")
    
    # IDÉE 3 : Choix du profil (Particulier / Entreprise)
    st.subheader("4. Vos Coordonnées")
    client_type = st.radio("Vous êtes :", ["Un Particulier", "Une Entreprise / Professionnel"], horizontal=True)
    
    # Formulaire final
    with st.form("client_form"):
        client_name = st.text_input("Nom complet *")
        
        # Si c'est une entreprise, on affiche magiquement les champs requis
        if client_type == "Une Entreprise / Professionnel":
            company_name = st.text_input("Nom de la Société *")
            siret = st.text_input("Numéro de SIRET *")
        else:
            company_name = "N/A"
            siret = "N/A"
            
        col_email, col_phone = st.columns(2)
        with col_email:
            client_email = st.text_input("Adresse E-mail *")
        with col_phone:
            client_phone = st.text_input("Téléphone *") 
        
        st.write("") 
        
        # Affichage du bandeau de prix dynamique
        if is_printable and volume_cm3 > 0:
            st.markdown(f"<div class='price-box'><h3 style='font-size: 14px; text-transform: uppercase;'>Estimation Instantanée</h3><h1 style='font-size: 38px;'>{final_price:.2f} € TTC</h1></div>", unsafe_allow_html=True)
            if discount_text:
                st.caption(f"<span style='color:#FFCC00;'>{discount_text}</span>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='price-box'><h3 style='font-size: 14px; text-transform: uppercase;'>Estimation Instantanée</h3><h1 style='font-size: 38px;'>0.00 € TTC</h1></div>", unsafe_allow_html=True)
        
        st.markdown("""
            <p style='font-size: 12px; color: #aaa; font-style: italic; text-align: center; margin-top: 12px; line-height: 1.4;'>
                ⚠️ <b>Note importante :</b> Ce montant inclut les options et frais de port mais fait office de simulation. 
                Chaque fichier est vérifié en interne par l'équipe <b>IDPAN3D</b>. 
                Vous recevrez une réponse définitive ainsi qu'un devis ferme sous 48 heures maximum.
            </p>
        """, unsafe_allow_html=True)
        
        st.write("") 
        submitted = st.form_submit_button("Envoyer le projet à l'atelier")
        
        if submitted:
            clean_phone = client_phone.replace(" ", "").replace(".", "").replace("-", "")
            email_is_valid = re.match(r"[^@]+@[^@]+\.[^@]+", client_email)

            if not uploaded_file:
                st.error("⚠️ Veuillez d'abord charger un fichier 3D.")
            elif not is_printable:
                st.error("⚠️ Votre fichier est hors dimensions, le devis ne peut pas être soumis en ligne. Merci de nous appeler au 06 78 22 57 76.")
            elif not client_name.strip():
                st.error("⚠️ Veuillez renseigner votre Nom.")
            elif client_type == "Une Entreprise / Professionnel" and (not company_name.strip() or not siret.strip()):
                st.error("⚠️ En tant que professionnel, le Nom de la société et le SIRET sont obligatoires.")
            elif not email_is_valid:
                st.error("⚠️ L'adresse e-mail semble invalide.")
            elif not clean_phone.isdigit() or len(clean_phone) != 10:
                st.error("⚠️ Le numéro de téléphone doit contenir exactement 10 chiffres.")
            elif len(set(clean_phone)) == 1 or clean_phone in ["1234567890", "0123456789"]:
                st.error("⚠️ Le numéro de téléphone saisi n'est pas valide.")
            else:
                try:
                    msg = MIMEMultipart()
                    msg['From'] = st.secrets["SMTP_EMAIL"]
                    msg['To'] = st.secrets["RECEIVER_EMAIL"]
                    msg['Subject'] = f"🆕 [{client_type.split()[1]}] Projet 3D - {client_name}"
                    
                    corps_email = f"""
                    Nouvelle demande sur IDPAN3D Portal :
                    
                    👤 INFORMATIONS CLIENT
                    -------------------------------------------
                    • Type de client : {client_type}
                    • Nom complet : {client_name}
                    • Entreprise : {company_name}
                    • SIRET : {siret}
                    • Email : {client_email}
                    • Tél : {client_phone}
                    
                    ⚙️ CONFIGURATION TECHNIQUE
                    -------------------------------------------
                    • Fichier : {uploaded_file.name}
                    • Dimensions : {dim_x:.2f} x {dim_y:.2f} x {dim_z:.2f} mm
                    • Volume : {volume_cm3:.2f} cm3
                    - Matière : {mat_choice}
                    - Finition : {qual_choice}
                    - Quantité : {qty} ex.
                    
                    📦 LOGISTIQUE & OPTIONS
                    -------------------------------------------
                    • Mode de livraison : {fdp_choice}
                    • Option Prioritaire 24h : {"OUI (Coût +30% inclus)" if urgency_option else "NON"}
                    • Code Promo utilisé : {promo_code if promo_code != "" else "Aucun"}
                    
                    💰 TARIFICATION SIMULÉE
                    -------------------------------------------
                    • TOTAL ESTIMÉ : {final_price:.2f} € TTC
                    """
                    
                    msg.attach(MIMEText(corps_email, 'plain', 'utf-8'))
                    
                    server = smtplib.SMTP(st.secrets["SMTP_SERVER"], st.secrets["SMTP_PORT"])
                    server.starttls()
                    server.login(st.secrets["SMTP_EMAIL"], st.secrets["SMTP_PASSWORD"])
                    server.sendmail(st.secrets["SMTP_EMAIL"], st.secrets["RECEIVER_EMAIL"], msg.as_string())
                    server.quit()
                    
                    st.success("✅ Parfait ! Votre demande a été transmise directement à l'atelier IDPAN3D.")
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'envoi de l'e-mail. Erreur: {e}")
                    
