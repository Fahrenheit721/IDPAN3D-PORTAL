import streamlit as st
import tempfile
from stl import mesh
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration de la page
st.set_page_config(page_title="IDPAN3D - Portail Client", page_icon="⚙️", layout="wide")

# CSS Personnalisé pour garder l'identité Noir et Jaune
st.markdown("""
    <style>
        .stApp { background-color: #111111; color: #ffffff; }
        h1, h2, h3 { color: #FFCC00; font-family: 'Arial', sans-serif; }
        .stButton>button { background-color: #FFCC00; color: #111111; font-weight: bold; width: 100%; border: none; }
        .stButton>button:hover { background-color: #ffffff; color: #111111; }
        .price-box { background-color: #FFCC00; color: #111111; padding: 20px; border-radius: 8px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# Titre Principal
st.markdown("<h1 style='text-align: center; font-size: 3rem;'>IDPAN3D PORTAL</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Devis et Production d'Impression 3D</p>", unsafe_allow_html=True)
st.divider()

# Création des deux colonnes
col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("1. Analyse du Fichier 3D")
    uploaded_file = st.file_uploader("Glissez votre fichier .STL ici", type=['stl'])
    
    volume_cm3 = 0
    dim_x = dim_y = dim_z = 0
    
    if uploaded_file is not None:
        # Streamlit a besoin de sauvegarder le fichier temporairement pour que numpy-stl le lise
        with tempfile.NamedTemporaryFile(delete=False, suffix='.stl') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
            
        try:
            stl_mesh = mesh.Mesh.from_file(tmp_path)
            
            # Calcul du volume et dimensions
            volume_mm3 = stl_mesh.get_mass_properties()[0]
            volume_cm3 = float(volume_mm3 / 1000.0)
            
            minx, maxx = stl_mesh.x.min(), stl_mesh.x.max()
            miny, maxy = stl_mesh.y.min(), stl_mesh.y.max()
            minz, maxz = stl_mesh.z.min(), stl_mesh.z.max()
            
            dim_x, dim_y, dim_z = float(maxx - minx), float(maxy - miny), float(maxz - minz)
            
            st.success(f"✅ Analyse réussie : {uploaded_file.name}")
            st.info(f"**Dimensions :** {dim_x:.2f} x {dim_y:.2f} x {dim_z:.2f} mm\n\n**Volume matière :** {volume_cm3:.2f} cm³")
            
        except Exception as e:
            st.error(f"Erreur de lecture du fichier STL : {e}")

with col2:
    st.subheader("2. Cahier des Charges")
    
    # Dictionnaires pour les prix
    mat_dict = {
        "🏠 Décoration / Maquette (PLA)": 0.15,
        "☀️ Extérieur / UV (ASA)": 0.25,
        "⚙️ Mécanique / Robuste (PETG-CF)": 0.30,
        "👟 Souple / Articulé (TPU)": 0.35
    }
    qual_dict = {
        "⚡ Rapide (0.28mm - Prototypes)": 1.0,
        "📐 Standard (0.20mm - Industriel)": 1.2,
        "🔍 Haute Fidélité (0.12mm - Précision)": 1.5
    }
    
    mat_choice = st.selectbox("Usage de la pièce (Matière)", list(mat_dict.keys()))
    qual_choice = st.selectbox("Qualité de finition", list(qual_dict.keys()))
    qty = st.number_input("Quantité", min_value=1, value=1)
    
    # Calcul du devis
    if volume_cm3 > 0:
        base_price = 15 + (volume_cm3 * mat_dict[mat_choice] * qual_dict[qual_choice])
        final_price = base_price * qty
        st.markdown(f"<div class='price-box'><h3>Estimation</h3><h1 style='color: #111;'>{final_price:.2f} € HT</h1></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='price-box'><h3>Estimation</h3><h1 style='color: #111;'>0.00 € HT</h1><small>Chargez un fichier STL</small></div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Formulaire Client
    with st.form("client_form"):
        st.subheader("3. Vos Coordonnées")
        client_name = st.text_input("Nom complet ou Raison Sociale *")
        client_email = st.text_input("Adresse E-mail *")
        client_phone = st.text_input("Téléphone")
        
        submitted = st.form_submit_button("Envoyer le projet à l'atelier")
        
        if submitted:
            if volume_cm3 == 0:
                st.error("⚠️ Veuillez d'abord charger un fichier 3D.")
            elif not client_name or not client_email:
                st.error("⚠️ Veuillez remplir votre Nom et votre E-mail.")
            else:
                # Envoi de l'e-mail avec st.secrets
                try:
                    msg = MIMEMultipart()
                    msg['From'] = st.secrets["SMTP_EMAIL"]
                    msg['To'] = st.secrets["RECEIVER_EMAIL"]
                    msg['Subject'] = f"🆕 Projet 3D - {client_name}"
                    
                    corps_email = f"""
                    Nouvelle demande sur IDPAN3D Portal :
                    
                    👤 CLIENT
                    - Nom : {client_name}
                    - Email : {client_email}
                    - Tél : {client_phone}
                    
                    ⚙️ TECHNIQUE
                    - Fichier : {uploaded_file.name}
                    - Dimensions : {dim_x:.2f} x {dim_y:.2f} x {dim_z:.2f} mm
                    - Volume : {volume_cm3:.2f} cm3
                    - Matière : {mat_choice}
                    - Qualité : {qual_choice}
                    - Quantité : {qty}
                    
                    💰 PRIX ESTIMÉ : {final_price:.2f} € HT
                    """
                    
                    msg.attach(MIMEText(corps_email, 'plain', 'utf-8'))
                    
                    server = smtplib.SMTP(st.secrets["SMTP_SERVER"], st.secrets["SMTP_PORT"])
                    server.starttls()
                    server.login(st.secrets["SMTP_EMAIL"], st.secrets["SMTP_PASSWORD"])
                    server.sendmail(st.secrets["SMTP_EMAIL"], st.secrets["RECEIVER_EMAIL"], msg.as_string())
                    server.quit()
                    
                    st.success("✅ Parfait ! Votre demande a été transmise directement à l'atelier IDPAN3D.")
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'envoi de l'e-mail. Vérifiez vos st.secrets. Erreur: {e}")