import streamlit as st
import spacy
import pdfplumber
from skill import *
from llm_helper import llm

from langchain_core.prompts import PromptTemplate

# Charger le modèle spaCy en français
nlp = spacy.load("fr_core_news_sm")

# Liste des compétences et niveaux d'études
competences_list = skills_list
niveaux_etudes = ['licence', 'master', 'doctorat', 'bac', 'bac+2', 'bac+5']

# Fonction pour extraire le texte d'un CV PDF
def extraire_texte_pdf(pdf_path):
    texte = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            texte += page.extract_text() or ""
    return texte

# Fonction pour extraire les informations
def extraire_informations(texte):
    doc = nlp(texte.lower())
    competences_trouvees = [c for c in competences_list if c in texte.lower()]
    niveau_etudes = [n for n in niveaux_etudes if n in texte.lower()]
    types_candidature = ['stage', 'alternance', 'cdi', 'cdd']
    type_candidature = [t for t in types_candidature if t in texte.lower()]
    return {"competences": competences_trouvees, "niveau_etudes": niveau_etudes, "type_candidature": type_candidature}

# Fonction de calcul du score ATS
def calculer_score_competences(competences_cv, competences_offre):
    if not competences_offre:
        return 0
    print(competences_cv)
    print(competences_offre)
    intersect_competences = [c for c in competences_cv if c in competences_offre]
    print(intersect_competences)
    
    return len(intersect_competences) / len(competences_offre)

# Fonction d'affichage esthétique
def afficher_recommandations(score):
    if score >= 0.8:
        st.success("🎯 Félicitations ! Votre CV correspond très bien à l'offre. Vous pouvez postuler en toute confiance. ✔️")
        st.info("💡 Conseil : Ajoutez une lettre de motivation personnalisée pour renforcer votre candidature.")
    elif score >= 0.5:
        st.warning("⚠️ Votre CV pourrait nécessiter des améliorations pour maximiser vos chances.")
        st.write("🔹 **Conseils d'amélioration :**")
        st.write("- **Ajoutez des compétences clés** mentionnées dans l'offre si vous les possédez.")
        st.write("- **Mettez en avant vos expériences et certifications** en lien avec le poste.")
        st.write("- **Utilisez un format de CV clair et lisible** par les ATS.")
    else:
        st.error("❌ Ce poste ne semble pas correspondre à votre profil.")
        st.write("📌 **Suggestions :**")
        st.write("- **Postulez à des offres plus alignées** avec vos compétences.")
        st.write("- **Améliorez votre CV** en acquérant de nouvelles compétences via des formations en ligne.")

# Fonction pour générer une lettre de motivation
def generateur(texte_cv, description_offre, competences_cv):
    template = '''
    En te basant sur la description du poste, le texte de ton CV, et les compétences mentionnées dans ton CV,
    crée une lettre de motivation professionnelle et concise.

    1. Utilise la description du poste suivante : {description_offre}
    2. Utilise le texte de CV suivante : {texte_cv}
    3. Mets en avant les compétences suivantes : {competences_cv}

    La lettre de motivation doit être formelle, concise, et mettre en avant les compétences du CV en lien avec le poste.
    Le but est de donner une impression positive et convaincante à l'employeur potentiel.
    '''

    # Création du template avec les valeurs passées
    pt = PromptTemplate.from_template(template)
    
    # Préparation des données d'entrée pour la chaîne de traitement
    chain = pt | llm
    response = chain.invoke(input={"texte_cv": texte_cv, "description_offre": description_offre, "competences_cv": competences_cv})
    
    return response.content


    
# Interface Streamlit
def main():
    #appliquer_css_personnalise()
    st.title("📄 ATS Checker : Testez votre CV contre une offre d'emploi")
    
    st.sidebar.header("🔍 Analysez votre CV")
    cv_file = st.sidebar.file_uploader("📂 Téléchargez votre CV (PDF)", type="pdf")
    description_offre = st.sidebar.text_area("✍️ Copiez la description de l'offre", height=150)
    
    if cv_file and description_offre:
        texte_cv = extraire_texte_pdf(cv_file)
        info_cv = extraire_informations(texte_cv)
        info_offre = extraire_informations(description_offre)
        score_competences = calculer_score_competences(info_cv['competences'], info_offre['competences'])
        
        if st.button("📊 Analyser le CV"):
            st.write("### 🏆 Résultats de l'analyse :")
            st.write(f"**🔹 Score ATS basé sur les compétences : {score_competences * 100:.2f}%**")
            
            competences_post = [c for c in info_cv['competences'] if c in info_offre['competences']]
            if len(competences_post) >=1:
                st.write("### 🛠️ Compétences que vous possédez pour ce poste :")
                st.write("- " + "\n- ".join(competences_post))
            else:
                st.write("❌ Aucune compétence correspondante trouvée dans votre CV.")
                
            
            afficher_recommandations(score_competences)
        
        if score_competences >0.8 :
            generer_lettre = st.selectbox(
                "Souhaitez-vous générer une lettre de motivation ?",
                options=["Non", "Oui"]
            )
            if generer_lettre == "Oui":
                # Générer la lettre de motivation en fonction du post sélectionné
                lettre_motivation = generateur(texte_cv,description_offre, info_cv['competences'])
                st.subheader("Lettre de Motivation Générée :")
                #st.text_area("Votre lettre de motivation", lettre_motivation, height=200)
                st.markdown(f"<div style='white-space: pre-wrap;'>{lettre_motivation}</div>", unsafe_allow_html=True)

            elif generer_lettre == "Non":
                st.write("Vous avez choisi de ne pas générer de lettre de motivation.")

if __name__ == "__main__":
    main()
