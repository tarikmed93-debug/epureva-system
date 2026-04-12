from database import init_db, ajouter_prospect
from emails import envoyer_mail

init_db()

ajouter_prospect(
    email="tarikmed93@gmail.com",
    etablissement="Restaurant Test",
    secteur="restaurant"
)

envoyer_mail("tarikmed93@gmail.com", "Restaurant Test", 1)
print("Test terminé — vérifie ta boîte mail !")
