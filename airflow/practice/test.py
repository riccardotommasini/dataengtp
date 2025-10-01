import requests, random
url = "https://www.dnd5eapi.co/api/2014/classes/warlock"
response = requests.get(url)
data = response.json()

proficiency_choices = data["proficiency_choices"][0]
number_choices = proficiency_choices["choose"]
proficiency_list = []

for pro in proficiency_choices["from"]["options"]:
    proficiency_list.append(pro["item"]["index"])

proficiency_chosen = []
for i in range(number_choices):
    choice = proficiency_list[random.randint(0,len(proficiency_list))]
    proficiency_chosen.append(choice)
    proficiency_list.remove(choice)

print(proficiency_chosen)