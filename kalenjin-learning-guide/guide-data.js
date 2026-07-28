export const corePhrases = [
  "Hello",
  "How are you?",
  "I am fine",
  "What is your name?",
  "My name is …",
  "How old are you?",
  "I am … years old",
  "Where are you?",
  "Where are you going?",
  "I want …",
  "Give me …",
  "I have … / I do not have …",
  "Thank you",
  "Goodbye / See you later",
];

const lines = (value) => value.split("|").map((item) => item.trim());
const vocab = (value) =>
  value.split("|").map((item) => {
    const [english, translation = ""] = item.split("~");
    return { english: english.trim(), translation: translation.trim() };
  });
const dialogue = (value) =>
  value.split("|").map((item) => {
    const [speakerA, speakerB] = item.split("~");
    return { speakerA: speakerA.trim(), speakerB: speakerB.trim() };
  });

export const weeks = [
  {
    title: "Greetings, Introductions, Family, and Identity",
    shortTitle: "Meet & greet",
    color: "coral",
    objectives: lines(
      "Greet someone politely|Say their name and ask another person’s name|Say their age and ask another person’s age|Name close family members|Say where they are from|Say goodbye politely",
    ),
    vocabulary: vocab(
      "hello~Chamge|good morning~Kainget komie?|good afternoon~Chamge|how are you?~yemune|I am fine~Achamege|my name is~Kainenyu ko Sheila|what is your name?~Kigureng’o|how old are you?|father|mother|brother|sister|grandmother|grandfather|family|I am from|goodbye|see you later",
    ),
    targets: lines(
      "Hello.|How are you?|I am fine.|What is your name?|My name is __.|How old are you?|I am __ years old.|Where are you from?|I am from __.|This is my father / mother.|Goodbye.|See you later.",
    ),
    dialogue: dialogue(
      "Hello.~Hello.|What is your name?~My name is __.|How old are you?~I am __ years old.|Where are you from?~I am from __.|Who is this?~This is my mother / father.",
    ),
    saturday: lines(
      "Welcome students and explain that the class will learn useful everyday Kalenjin step by step.|Do a greeting circle and have each student repeat the greetings with gestures and eye contact.|Teach the family words using pictures or simple drawings.|Model a short partner introduction and let students practice in pairs.|Play a greeting ball game: whoever catches the ball must greet and introduce themselves.",
    ),
    midweek: lines(
      "Greeting drill with fast repetition|Each child introduces themselves without reading|Family word review|Question time for students and parents",
    ),
    homework: lines(
      "Practice introducing yourself to one family member.|Memorize the greeting and name phrases.|Draw your family and label the relatives in English, leaving room to add Kalenjin later.",
    ),
  },
  {
    title: "Numbers, Body Parts, and Clothing",
    shortTitle: "Count & move",
    color: "gold",
    objectives: lines(
      "Count from 1 to 20 confidently|Identify major body parts|Name common clothing items|Say what they are wearing|Ask where an item of clothing is",
    ),
    vocabulary: vocab(
      "numbers 1–20|head|eyes|ears|nose|mouth|hand|leg|foot|hair|nails|shirt|dress|trousers|skirt|shoes|hat|sweater|shuka / traditional wear",
    ),
    targets: lines(
      "What is this?|This is my hand.|These are my shoes.|Where is your hat?|My hat is here.|I am wearing __.|He is wearing __.|She is wearing __.",
    ),
    dialogue: dialogue(
      "What is this?~This is my hand.|What are you wearing?~I am wearing shoes.|Where is your hat?~My hat is here.",
    ),
    saturday: lines(
      "Review greetings, names, and age from Week 1.|Count together from 1 to 10, then 1 to 20.|Teach body parts by pointing to them and having the class copy.|Teach clothing items using pictures or real items.|Play Simon Says using body parts and clothing words.",
    ),
    midweek: lines(
      "Counting challenge|Body-part pointing drill|Clothing description practice|Pronunciation correction",
    ),
    homework: lines(
      "Count 1–20 daily.|Name 5 body parts and 5 clothing items.|Practice saying: I am wearing __.",
    ),
  },
  {
    title: "Location, Movement, and Possessions",
    shortTitle: "Here & there",
    color: "cyan",
    objectives: lines(
      "Say where they are|Ask where someone is|Say where they are going|Ask where someone is going|Say where something is|Say whether they have something",
    ),
    vocabulary: vocab(
      "here|there|over there|home|school|church|shop|road|where|go|come|yesterday|tomorrow|book|bag|shoes|phone|mine",
    ),
    targets: lines(
      "Where are you?|I am at home.|I am here.|Where are you going?|I am going to school.|Do you want to come?|Come with me.|Where is my bag?|It is here / there.|I have it.|I do not have it.|Where were you yesterday?|Where will you go tomorrow?",
    ),
    dialogue: dialogue(
      "Where are you?~I am at home.|Where are you going?~I am going to church.|Do you want to come?~Yes / No.|Where is my book?~It is here.|Do you have it?~I have it / I do not have it.",
    ),
    saturday: lines(
      "Use the room space to show here, there, come, and go.|Teach place words such as home, school, church, and shop.|Model short movement dialogues and object-location dialogues.|Hide a classroom object and ask students to say where it is.|Use pair practice for: Where are you? Where are you going?",
    ),
    midweek: lines(
      "Phone-style conversation practice: Where are you?|Object location practice|Yesterday/tomorrow challenge for older students|Extra support for shy learners",
    ),
    homework: lines(
      "Practice: I am here. I am at home. I am going to __.|Ask a family member where an object is.",
    ),
  },
  {
    title: "Food, Hunger, Thirst, and Mealtime",
    shortTitle: "Share a meal",
    color: "leaf",
    objectives: lines(
      "Ask whether someone has eaten|Say whether they are hungry or full|Ask for water|Offer food or water|Name common foods and drinks|Describe drinks as hot, warm, or cold",
    ),
    vocabulary: vocab(
      "food|eat|hungry|full|water|tea|milk|meat|maize|beans|rice|bread|vegetables|cold|warm|hot|enough",
    ),
    targets: lines(
      "Have you eaten?|I have eaten.|I have not eaten.|Are you hungry?|I am hungry.|I am full.|I want food.|I am preparing food.|I am eating.|That is enough food.|Do you want water?|Give me water.|The water is cold / warm / hot.",
    ),
    dialogue: dialogue(
      "Have you eaten?~No, I have not eaten.|Are you hungry?~Yes, I am hungry.|Do you want water?~Yes, give me water.|Is it cold?~Yes, it is cold.",
    ),
    saturday: lines(
      "Review place and possession questions from Week 3.|Teach the food and drink words using pictures or real items if available.|Model a mealtime dialogue and have students repeat in pairs.|Practice asking for water politely.|Do a short mealtime role play with serving and answering.",
    ),
    midweek: lines(
      "Food naming challenge|Pair practice: Have you eaten?|Hot / warm / cold speaking drill|Questions and catch-up practice",
    ),
    homework: lines(
      "Name foods at dinner in Kalenjin if possible.|Practice asking for water politely.",
    ),
  },
  {
    title: "Daily Actions, Songs, Dance, Play, and Exercise",
    shortTitle: "Act it out",
    color: "violet",
    objectives: lines(
      "Name common daily actions|Say what they are doing|Invite someone to play, sing, dance, or run|Say what activities they like",
    ),
    vocabulary: vocab(
      "run|walk|jump|sing|dance|play|sit|stand|sleep|wake up|eat|go|come|like|today",
    ),
    targets: lines(
      "I am running.|I am dancing.|I am singing.|Do you want to play?|Come, let us go.|Let us sing.|Let us dance.|I like running.|I like singing.",
    ),
    dialogue: dialogue(
      "What are you doing?~I am running.|Do you want to play?~Yes, let us play.|Do you like dancing?~Yes, I like dancing.",
    ),
    saturday: lines(
      "Review food and water language briefly.|Teach verbs through movement so the class can act them out.|Model the present action sentence pattern: I am __ing.|Use pair work where one student acts and the other says the action.|End with a simple chant or song.",
    ),
    midweek: lines(
      "Action review|Call-and-response commands|Like / do not like practice for older students|Pronunciation correction",
    ),
    homework: lines(
      "Say 5 daily actions during the day.|Teach one action phrase to a family member.",
    ),
  },
  {
    title: "Animals and Home Animals",
    shortTitle: "Animal talk",
    color: "orange",
    objectives: lines(
      "Name common home and farm animals|Ask what animal something is|Say whether they have an animal at home|Describe an animal as big or small|Ask where an animal is",
    ),
    vocabulary: vocab(
      "cow|calf|goat|sheep|donkey|dog|cat|chicken|milk|meat|big|small|where|home",
    ),
    targets: lines(
      "What animal is this?|This is a cow.|Do you have a dog?|Yes, I have a dog.|No, I do not have a dog.|Where is the goat?|The goat is here / there.|The cow is big.|The cat is small.",
    ),
    dialogue: dialogue(
      "What animal is this?~This is a goat.|Do you have a goat at home?~No, I do not.|Do you have a dog?~Yes, I do.|Where is the goat?~It is there.",
    ),
    saturday: lines(
      "Review action verbs with movement.|Teach animal names with picture cards.|Add size words such as big and small.|Model animal conversations and let students answer from picture prompts.|Play Animal Corners using images around the room.",
    ),
    midweek: lines(
      "Animal naming speed round|Big/small description practice|Where is the animal? question drill|Support for memory and pronunciation",
    ),
    homework: lines(
      "Memorize 5 animals.|Practice asking: Do you have a dog / cat?",
    ),
  },
  {
    title: "Plants, Crops, Trees, and Farming Vocabulary",
    shortTitle: "Grow & harvest",
    color: "leaf",
    objectives: lines(
      "Name common crops and plants|Say what is growing|Identify simple farm actions|Ask where the farm is|Say whether the farm is big or small",
    ),
    vocabulary: vocab(
      "maize|beans|tea|cabbage|vegetables|calabash|tree|grass|farm / shamba|plant|grow|weed|harvest|big|small",
    ),
    targets: lines(
      "This is maize.|This is tea.|What is growing?|Maize is growing.|We are planting.|We are harvesting.|Where is the farm?|The farm is there.|The farm is big.",
    ),
    dialogue: dialogue(
      "What is this?~This is maize.|What is growing here?~Cabbage is growing.|Where is the farm?~The farm is there.|Is the farm big?~Yes, it is big.",
    ),
    saturday: lines(
      "Review animals and size words.|Teach crop and plant vocabulary with photos or drawings.|Model simple farm-talk dialogues.|Do pair picture description.|Run a farm walk role play where students identify what is growing.",
    ),
    midweek: lines(
      "Crop flashcard review|Planting and harvesting action practice|Older students answer: What is growing on the farm?|Questions and recap",
    ),
    homework: lines(
      "Learn 5 crop words.|Ask older relatives which crops they know or grew.",
    ),
  },
  {
    title: "Places, Rift Valley Locations, and Visiting",
    shortTitle: "Places & visits",
    color: "cyan",
    objectives: lines(
      "Name familiar places|Say where they want to go|Ask whether someone has been to a place|Say whether a place is near or far|Talk about home areas like Eldoret, Kesses, and Lessos",
    ),
    vocabulary: vocab(
      "place|town|market|church|school|home|Eldoret|Kesses|Lessos|near|far|go|come|visit|have been",
    ),
    targets: lines(
      "I want to go to __.|Have you been to __?|Yes, I have been there.|No, I have not been there.|It is near.|It is far.|We are going to __.",
    ),
    dialogue: dialogue(
      "Where do you want to go?~I want to go to Eldoret.|Have you been to Kesses?~Yes, I have.|Is it near or far?~It is near / far.",
    ),
    saturday: lines(
      "Review farm and plant words.|Introduce common places first, then specific Rift Valley locations relevant to the class.|Model place and travel dialogues.|Use a simple map or printed place names.|Practice speaking in lines or partner rotations.",
    ),
    midweek: lines(
      "Pronunciation of place names|Have you been to __? practice|Older students explain where family is from|Open question time",
    ),
    homework: lines(
      "Ask family members which places in Rift Valley are important to your family.|Practice: I want to go to __.",
    ),
  },
  {
    title: "Shop and Market Role Play",
    shortTitle: "Market day",
    color: "gold",
    objectives: lines(
      "Ask for an item in a shop|Choose between items|Say I want this|Ask a simple price question if desired|Use polite buyer and seller phrases",
    ),
    vocabulary: vocab(
      "shop|market|buy|sell|food|water|bread|milk|meat|beans|rice|this|that|give me|how much?|enough|thank you",
    ),
    targets: lines(
      "I want __.|Give me __.|I want this one.|Not that one.|How much?|That is enough.|Thank you.",
    ),
    dialogue: dialogue(
      "Hello.~Hello.|Give me bread and milk.~Here it is.|How much?~__.|Thank you.~You are welcome.",
    ),
    saturday: lines(
      "Review place and travel language.|Teach item words likely found in a small shop or market.|Model a short buyer-seller dialogue on the board.|Let students practice as buyer and seller.|Set up a pretend shop with objects or picture cards.",
    ),
    midweek: lines(
      "Slow repeated role-play practice|Confidence-building for shy students|Older students extend with more than one item|Pronunciation support",
    ),
    homework: lines(
      "Memorize one full buyer-seller dialogue.|Practice saying: I want this one.",
    ),
  },
  {
    title: "Life in the Shamba",
    shortTitle: "Life on the farm",
    color: "orange",
    objectives: lines(
      "Ask what is growing on the farm|Ask where the land is|Ask how big the land is|Describe basic farming actions|Talk about planting and harvesting",
    ),
    vocabulary: vocab(
      "land|farm|grow|plant|plow|harrow|weed|harvest|big|small|where|who|maize|beans|tea",
    ),
    targets: lines(
      "What is growing on the farm?|Maize is growing.|Where is the land?|The land is in __.|How big is the land?|It is big / small.|We are plowing.|We are planting.|We are harvesting.",
    ),
    dialogue: dialogue(
      "Where is the farm?~The farm is in __.|What is growing there?~Maize and beans are growing.|Is the land big?~Yes, it is big.|What are you doing?~We are planting.",
    ),
    saturday: lines(
      "Review the market role play briefly.|Teach farmland and farm-work vocabulary.|Model a visitor-farmer conversation.|Use an image or imaginary family farm for description practice.|Let students do farm role plays in pairs.",
    ),
    midweek: lines(
      "Question practice about farm size and location|Longer answers for older students|Question and answer time for difficult farm words|Pronunciation review",
    ),
    homework: lines(
      "Ask a family member about farm work they know.|Practice saying 3 farm action phrases.",
    ),
  },
  {
    title: "Household Items, Cleaning, and Cultural Topic: Age Sets",
    shortTitle: "Home & culture",
    color: "violet",
    objectives: lines(
      "Name common household items|Say where household items are|Say what cleaning action they are doing|Learn that age sets are an important cultural topic",
    ),
    vocabulary: vocab(
      "house|room|chair|table|bed|cup|plate|pot|spoon|broom|bucket|clean|sweep|wash|bring|where|here|there",
    ),
    targets: lines(
      "Where is the broom?|It is here.|Bring the bucket.|I am cleaning the house.|I am sweeping.|I am washing the cup.|The plate is there.",
    ),
    dialogue: dialogue(
      "Where is the broom?~It is there.|Bring the broom.~Here it is.|What are you doing?~I am cleaning the house.|What are you washing?~I am washing the cup.",
    ),
    saturday: lines(
      "Review farm language.|Teach household items with pictures or actual objects.|Model short cleaning-the-house dialogues.|Use pair practice with object requests and locations.|Give a short, age-appropriate cultural note on age sets without letting it replace language practice.",
    ),
    midweek: lines(
      "Household item review|Command-and-response practice|Short culture discussion in English|Questions and recap",
    ),
    homework: lines(
      "Name 5 household items at home.|Say one cleaning sentence in Kalenjin.",
    ),
  },
  {
    title: "Cooking, Utensils, Final Review, and Conversation Showcase",
    shortTitle: "Celebrate & speak",
    color: "coral",
    objectives: lines(
      "Name common cooking and eating tools|Ask for items used in cooking|Say simple cooking actions|Combine earlier vocabulary in conversation|Complete a short final role play",
    ),
    vocabulary: vocab(
      "pot|spoon|knife|plate|cup|water|food|fire / stove|cook|ready|eat|bring|give me",
    ),
    targets: lines(
      "Bring the pot.|Give me the spoon.|I am cooking.|The food is ready.|Let us eat.|Do you want water?|Give me a plate.",
    ),
    dialogue: dialogue(
      "What are you doing?~I am cooking.|Bring the pot.~Here is the pot.|Give me water.~Here is the water.|Is the food ready?~Yes, the food is ready.",
    ),
    saturday: lines(
      "Review core phrases from the entire course.|Teach cooking tools and eating utensils.|Model a short cooking dialogue.|Run final role-play stations: introduction, travel, food, market, farm, and home.|End with praise, celebration, and a short speaking showcase for each student.",
    ),
    midweek: lines(
      "Final review|Support shy students before the conversation showcase|Answer last questions|Encourage home practice",
    ),
    homework: lines(
      "Review all weekly core phrases.|Practice one full conversation at home.",
    ),
  },
];

export const assessments = [
  {
    title: "Checkpoint after Week 4",
    afterWeek: 4,
    items: lines(
      "Greet politely|Say name and age|Say where they are from|Answer simple food or hunger questions",
    ),
  },
  {
    title: "Checkpoint after Week 8",
    afterWeek: 8,
    items: lines(
      "Ask where someone is going|Ask where something is|Talk about places|Ask for food or water",
    ),
  },
  {
    title: "Final check in Week 12",
    afterWeek: 12,
    items: lines(
      "Do a short greeting|Give a simple self-introduction|Say one family statement|Ask one location question|Make one food or water request|Take part in one short role play",
    ),
  },
];
