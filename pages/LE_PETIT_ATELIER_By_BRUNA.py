import pandas as pd
import streamlit as st
import os
import base64
import pathlib
from io import BytesIO



def chiffres_affaires():
    st.title("2244 - LE PETIT ATELIER By BRUNA : Nettoyage du Chiffres d'Affaires")
    # Chargement du fichier Excel
    uploaded_file = st.file_uploader("Téléchargez votre fichier", type=["csv"])

    if uploaded_file is not None:
        # Vérification de l'extension du fichier
        if uploaded_file.type == 'text/csv':
            # Lecture du fichier CSV
            df = pd.read_csv(uploaded_file, dtype=str)
        else:
            st.error("Format de fichier non pris en charge.")
            return

        # Effectuer le nettoyage des données avec pandas
        # ATTENTION Certains 'Prénoms' contiennent 'NaN' et le nom 'De passage', mais ont des valeurs Produits et Prestation : à voir avec Erine si pose problème ou non
        # ...
        df = df.rename(columns=lambda x: x.replace("(", "").replace(")", "").replace("€", "").rstrip())
        df['N°compte'] = df.apply(lambda row: "C" + str(row['Nom'])[:3] + str(row['Prénom'])[:3], axis=1)
        df['Libellé'] = df.apply(lambda row: f"{row['Nom']} {row['Prénom']} {row['Type']}", axis=1)
        df_short = df[["Date ticket", "N°ticket", "N°compte", "Libellé", "Type", "Total TTC", "TVA", "Total HT"]]
        df_short = df_short.dropna()


        #Créer 3 dataframes pour disposition type Bilan
        df_TTC = df_short.copy()
        df_TTC['Débit']=df_TTC['Total TTC']
        df_TTC['Crédit']=''
        df_TTC.drop(['Total TTC', 'TVA', 'Total HT'], axis=1, inplace=True)

        df_HT = df_short.copy()
        df_HT['Débit']=''
        df_HT['Crédit']=df_HT['Total HT']
        df_HT.drop(['Total TTC', 'TVA', 'Total HT'], axis=1, inplace=True)
        df_HT.loc[df_HT['Type'] == 'Prestation', 'N°compte'] = 706
        df_HT.loc[df_HT['Type'] == 'Produit', 'N°compte'] = 707
        df_HT.loc[~df_HT['Type'].isin(['Prestation', 'Produit']), 'N°compte'] = 471

        df_TVA = df_short.copy()
        df_TVA['Débit']=''
        df_TVA['Crédit']=df_TVA['TVA']
        df_TVA.drop(['Total TTC', 'TVA', 'Total HT'], axis=1, inplace=True)
        df_TVA['N°compte'] = df_TVA['N°compte'].replace(to_replace='.*', value=44571, regex=True)


        # Ajouter une colonne "Index_Origine" contenant les index d'origine de chaque dataframe
        df_TTC['Index_Origine'] = df_TTC.index
        df_HT['Index_Origine'] = df_HT.index
        df_TVA['Index_Origine'] = df_TVA.index

        # Créer une colonne "Dataframe_Type" pour indiquer le type de chaque dataframe
        df_TTC['Dataframe_Type'] = 'TTC'
        df_HT['Dataframe_Type'] = 'HT'
        df_TVA['Dataframe_Type'] = 'TVA'

        # Concaténer les dataframes
        df_concat = pd.concat([df_TTC, df_HT, df_TVA])

        # Définissez l'ordre des catégories
        ordre_categories = ['TTC', 'HT', 'TVA']

        # Créez une catégorie personnalisée avec l'ordre spécifié
        df_concat['Dataframe_Type'] = pd.Categorical(df_concat['Dataframe_Type'], categories=ordre_categories, ordered=True)


        # Trier les lignes en utilisant l'ordre des index d'origine
        df_concat = df_concat.sort_values(by=['Index_Origine','Dataframe_Type'])

        # Supprimer la colonne "Dataframe_Type" & "Index_Origine"
        df_concat.drop(['Dataframe_Type','Index_Origine', 'Type'], axis=1, inplace=True)

        # Afficher les données nettoyées dans l'interface utilisateur
        st.dataframe(df_concat)

        # Télécharger le fichier nettoyé
        cleaned_file = BytesIO()
        df_concat.to_excel(cleaned_file, index=False)
        cleaned_file.seek(0)

        # Afficher le lien de téléchargement avec le chemin spécifié
        filename, extension = os.path.splitext(uploaded_file.name)
        download_filename = f"cleaned_{filename}.xlsx"
        st.markdown(f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{base64.b64encode(cleaned_file.getvalue()).decode()}" download="{download_filename}" target="_blank">Télécharger le fichier nettoyé</a>', unsafe_allow_html=True)

def reglements():
    st.title("2244 - LE PETIT ATELIER By BRUNA : Nettoyage des Règlements")
    uploaded_file = st.file_uploader("Téléchargez votre fichier", type=["csv"])

    if uploaded_file is not None:
        # Vérification de l'extension du fichier
        if uploaded_file.type == 'text/csv':
            # Lecture du fichier CSV
            df = pd.read_csv(uploaded_file, dtype=str, skiprows=2, header=None)
        else:
            st.error("Format de fichier non pris en charge.")
            return
        
        # ATTENTION Certains Statuts = Crédit d'annulation, Donc valeurs négatifs dans crédit et débit, à voir avec Erine
        column_names = ["Date", "N°règlement", "Encaissé par", "Pièce", "Nom", "Prénom", "Date de naissance", "Genre", "Origine", "Mobile", "Email", "Statut", "CB", "Espèces", "Chèques", "Autres", "Total hors chèques cadeaux", "Chèques cadeaux", "Total réglé", "Impayés"]
        df.columns = column_names
        df['N°compte'] = df.apply(lambda row: "C" + str(row['Nom'])[:3] + str(row['Prénom'])[:3], axis=1)
        df['Libellé'] = df.apply(lambda row: f"{row['Nom']} {row['Prénom']}", axis=1)
        df_short = df[["Date", "Pièce", "N°compte", "Libellé", "CB", "Espèces", "Chèques", "Autres", "Chèques cadeaux", "Total réglé"]]
        df_short = df_short.dropna()
        df_short['Pièce'] = df_short['Pièce'].astype(int)

        df_TTC = df_short.copy()
        df_CB = df_short.copy()
        df_CHQ = df_short.copy()

        df_TTC['Débit']=''
        df_TTC['Crédit']=df_TTC['Total réglé']
        df_TTC.drop(["CB", "Espèces", "Chèques", "Autres", "Chèques cadeaux", "Total réglé"], axis=1, inplace=True)
        
        
        debit_columns = ['CB', 'Espèces', 'Chèques', 'Autres']

        # Fonction personnalisée pour calculer le débit
        def calculate_debit(row):
            # Vérifiez si la valeur de chaque colonne est différente de '0,00'
            # Si c'est le cas, renvoyez la valeur, sinon renvoyez NaN (ou une valeur appropriée selon vos besoins)
            for column in debit_columns:
                if row[column] != '0,00':
                    return row[column]
            return pd.NA  # Utilisez None à la place de pd.NA si vous utilisez une version de pandas antérieure à 1.0
        df_CB['Débit']=df_CB.apply(calculate_debit, axis=1)
        df_CB['Crédit']=''

        # Fonction personnalisée pour modifier la valeur de N°compte
        def modify_numero_compte(row):
            for column in debit_columns:
                if row[column] != '0,00':
                    if column == 'CB':
                        return '583'
                    elif column == 'CB en ligne':
                        return '4671'
                    elif column == 'Espèces':
                        return '531'
                    elif column == 'Chèques':
                        return '582'
                    elif column == 'Autres':
                        return '586'
            return row['N°compte']

        # Appliquer la fonction modify_numero_compte à chaque ligne du DataFrame pour modifier la colonne 'N°compte'
        df_CB['N°compte'] = df_CB.apply(modify_numero_compte, axis=1)
        df_CB.drop(["CB", "Espèces", "Chèques", "Autres", "Chèques cadeaux", "Total réglé"], axis=1, inplace=True)


        df_CHQ['Débit']=df_CHQ['Chèques cadeaux']
        df_CHQ['Crédit']=''
        df_CHQ['N°compte'] = df_CHQ['N°compte'].replace(to_replace='.*', value=4673, regex=True)
        df_CHQ.drop(["CB", "Espèces", "Chèques", "Autres", "Chèques cadeaux", "Total réglé"], axis=1, inplace=True)

        # Ajouter une colonne "Index_Origine" contenant les index d'origine de chaque dataframe
        df_TTC['Index_Origine'] = df_TTC.index
        df_CB['Index_Origine'] = df_CB.index
        df_CHQ['Index_Origine'] = df_CHQ.index

        # Créer une colonne "Dataframe_Type" pour indiquer le type de chaque dataframe
        df_TTC['Dataframe_Type'] = 'TTC'
        df_CB['Dataframe_Type'] = 'HT'
        df_CHQ['Dataframe_Type'] = 'CHQ'

        # Concaténer les dataframes
        df_concat = pd.concat([df_TTC, df_CB, df_CHQ])

        # Définissez l'ordre des catégories
        ordre_categories = ['TTC', 'HT', 'CHQ']

        # Créez une catégorie personnalisée avec l'ordre spécifié
        df_concat['Dataframe_Type'] = pd.Categorical(df_concat['Dataframe_Type'], categories=ordre_categories, ordered=True)


        # Trier les lignes en utilisant l'ordre des index d'origine
        df_concat = df_concat.sort_values(by=['Index_Origine','Dataframe_Type'])

        # Supprimer la colonne "Dataframe_Type" & "Index_Origine"
        df_concat.drop(['Dataframe_Type','Index_Origine'], axis=1, inplace=True)

        # Afficher les données nettoyées dans l'interface utilisateur
        st.dataframe(df_concat)

        # Télécharger le fichier nettoyé
        cleaned_file = BytesIO()
        df_concat.to_excel(cleaned_file, index=False)
        cleaned_file.seek(0)

        # Afficher le lien de téléchargement avec le chemin spécifié
        filename, extension = os.path.splitext(uploaded_file.name)
        download_filename = f"cleaned_{filename}.xlsx"
        st.markdown(f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{base64.b64encode(cleaned_file.getvalue()).decode()}" download="{download_filename}" target="_blank">Télécharger le fichier nettoyé</a>', unsafe_allow_html=True)

def chaques_cadeaux():
    st.title("2244 - LE PETIT ATELIER By BRUNA : Nettoyage des Chèques-Cadeaux")

    # Chargement du fichier Excel
    uploaded_file = st.file_uploader("Téléchargez votre fichier", type=["csv"])

    if uploaded_file is not None:
        # Vérification de l'extension du fichier
        if uploaded_file.type == 'text/csv':
            # Lecture du fichier CSV
            df = pd.read_csv(uploaded_file, dtype=str)
        else:
            st.error("Format de fichier non pris en charge.")
            return

def fonds_caisse():
    st.title("2244 - LE PETIT ATELIER By BRUNA : Nettoyage des Fonds de Caisse")

    # Chargement du fichier Excel
    uploaded_file = st.file_uploader("Téléchargez votre fichier", type=["csv"])

    if uploaded_file is not None:
        # Vérification de l'extension du fichier
        if uploaded_file.type == 'text/csv':
            # Lecture du fichier CSV
            df = pd.read_csv(uploaded_file, dtype=str)
        else:
            st.error("Format de fichier non pris en charge.")
            return



def main():
    st.sidebar.title("Navigation")
    pages = {
        "Chiffres d'affaires": chiffres_affaires,
        "Règlements" : reglements,
        "Chèques cadeaux" : chaques_cadeaux,
        "Fonds de caisse" : ""
    }
    selection = st.sidebar.radio("Aller à", list(pages.keys()))

    if selection == "Chiffres d'affaires":
        chiffres_affaires()
    elif selection == "Règlements":
        reglements()
    elif selection == "Chèques cadeaux":
        chaques_cadeaux()
    elif selection == "Fonds de caisse":
        fonds_caisse()

if __name__ == "__main__":
    main()