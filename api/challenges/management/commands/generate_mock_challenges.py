import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.core import serializers

from api.users.models import UserProfile, APIUserState
from api.challenges.models import Obstacle, ObstacleTask, ChallengeXPBaseline, Challenge, ChallengeCategory, ChallengeColorProfile

class Command (BaseCommand):
    help = "Make some challenges for testing."

    challenge_metadata = [
        { # 1
            "name": 'Neon Angels on the Road to Ruin',
            "description": "No one here gets out alive / Pushing power in overdrive / Cobra kings wet and wild / Love the devil that's in your smile // Let me tell you what we've been doin' / Neon angels on the road to ruin" },
        { # 2
            "name": "Double Dare Ya",
            "description": "Is that supposed to be doing that? / Ok, sorry, ok we're starting now / We're Bikini Kill and we want revolution / Girl-style now!" },
        { # 3
            "name": "Don't Let Me Be Misunderstood",
            "description": "Baby, do you understand me now / Sometimes I feel a little mad / Well don't you know that no-one alive / Can always be an angel / When things go wrong I seem to be bad" },
        { # 4
            "name": "Walk On By",
            "description": "If you see me walking down the street / And I start to cry, each time we meet / Walk on by / Walk on by / Make believe that you don't see the tears / Just let me grieve / In private, 'cause each time I see you, I break down and cry" },
        { # 5
            "name": "Anything You Can Do (I Can Do Better)",
            "description": "I can shoot a partridge, with a single cartridge. / I can get a sparrow, with a bow and arrow. / I can live on bread and cheese. / And only on that? / Yes. / So can a rat! // Any note you can reach, I can go higher. / I can sing anything higher than you." },
        { # 6
            "name": "All of Me",
            "description": "You took my kisses and all my love / You taught me how to care / Am I to be just remnant of a one side love affair // All you took / I gladly gave / There is nothing left for me to save // All of me / Why not take all of me" },
        { # 7
            "name": "Bills, Bills, Bills",
            "description": "At first we started out real cool / Taking me places I ain't never been / But now, you're getting comfortable / Ain't doing those things you did no more / You're slowly making me pay for things / Your money should be handling" },
        { # 8
            "name": "9 to 5",
            "description": "Well, I tumble outta bed and stumble to the kitchen / Pour myself a cup of ambition / Yawn and stretch and try to come to life" },
        { # 9
            "name": "Make Your Own Kind of Music",
            "description": "Nobody can tell ya / There's only one song worth singing / They may try and sell ya / 'Cause it hangs them up / To see someone like you // But you gotta make your own kind of music / Sing your own special song / Make your own kind of music / Even if nobody else sings along" },
        { # 10
            "name": "Downtown",
            "description": "When you're alone and life is making you lonely / You can always go / Downtown / When you've got worries all the noise and the hurry / Seems to help I know / Downtown // Just listen to the music of the traffic in the city / Linger on the sidewalk where the neon signs are pretty" },
        { # 11
            "name": "Upside Down",
            "description": "I said upside down / You're turning me / You're giving love instinctively / Around and round you're turning me // Upside down / Boy, you turn me / Inside out / And round and round / Upside down / Boy, you turn me / Inside out / And round and round" },
        { # 12
            "name": "Pretend We're Dead",
            "description": "What's up with what's going down / In every city, in every town / Cramping styles is the plan / They've got us in the palm of every hand" },
        { # 13
            "name": "These Days",
            "description": "I've been out walking / I don't do too much talking these days / These days / These days I seem to think a lot / About the things that I forgot to do / And all the times I had / A chance to" },
        { # 14
            "name": "Hit or Miss",
            "description": "Can’t you see / I gotta be me / Ain’t nobody / Just like this / I gotta be me / Baby hit or miss // Sitting here / All by myself / Trying to be / Everybody else // Can’t you see I gotta be me / Ain’t nobody just like this / I gotta be me / Baby hit or miss" },
        { # 15
            "name": "Rock Steady",
            "description": "Rock steady, baby / That's what I feel now / Let's call this song exactly what it is / Step and move your hips / With a feeling from side to side / Sit yourself down in your car / And take a ride / And while you're moving / Rock steady / Rock steady, baby" },
        { # 16
            "name": "Bam Bam",
            "description": "Mi seh one ting Nancy kyaahn understand / One ting Nancy kyaahn understand / Wha mek dem a taak bout mi ambition? / Seh, what makes dem a taak bout mi ambition? / Some a dem a aks mi weh mi get it fram / Some of them ask me where me get it from / A chuu dem nuh know it's fram creation / A chuu dem nuh know it's fram creation" },
        { # 17
            "name": "I'm in the Band",
            "description": "I can see what you're going to say to me / If I don't explain it away / I'm in the band / And I deserve to be here and I do anyway // Alright, alright / Alright, alright // We don't listen to what you say / Girls get busy / Not in the way / Girls make music / We're here to stay" },
        { # 18
            "name": "Multiply And Divide",
            "description": "Put the keys to the car / Then they'll know that someone sits inside / Put a flag on the back / Then they'll see you've got American pride / Keep your eyes on the ground / Chemicals gonna keep you from those lies / Now you're part of the plan that they've got / Get your peas in a pod and you'll / Multiply then divide" } ]

    def handle (this, *args, **kwargs):
        random.shuffle (this.challenge_metadata)

        authors = list (UserProfile.objects.filter (api_user__state=APIUserState.ACTIVE))
        categories = list (ChallengeCategory.objects.all ())
        challenge_durations = [timedelta (days=1), timedelta (days=7), timedelta (days=28)]
        color_profiles = list (ChallengeColorProfile.objects.all ())

        tasks = list (ObstacleTask.objects.all ())
        obstacle_durations = [{'value': 'D', 'days': 1}, {'value': 'W', 'days': 7}, {'value': 'M', 'days': 28}]
        subcategories = list (ChallengeCategory.objects.exclude (name='Mixed'))

        xp_values = {}
        for xp in ChallengeXPBaseline.objects.all ():
            if not xp.duration_days in xp_values:
                xp_values [xp.duration_days] = []

            xp_values [xp.duration_days].append (xp.xp_baseline)

        sequenced_markers = {
            7: { 'D': False },
            28: { 'D': False, 'W': False } }

        for (metadata, challenge_duration, i) in zip (this.challenge_metadata, challenge_durations * 6, range (18)):
            xp_value = random.choice (xp_values [challenge_duration.days])

            challenge = Challenge (
                author=random.choice (authors),
                category=random.choice (categories),
                name=metadata ['name'],
                description=metadata ['description'],
                duration=challenge_duration,
                color_profile=random.choice (color_profiles),
                xp_value=xp_value,
                external_url='https://www.tiktok.com/@happyandhealthyolivia/video/6987448756409060614')

            challenge.save ()

            if challenge_duration.days == 1:
                obstacle_duration = obstacle_durations [0]
            elif challenge_duration.days == 7:
                obstacle_duration = obstacle_durations [i//3 % 2]
            else:
                obstacle_duration = obstacle_durations [i//3 % 3]

            if obstacle_duration ['days'] == challenge_duration.days:
                sequenced_obstacles = False
            elif not sequenced_markers [challenge_duration.days] [obstacle_duration ['value']]:
                sequenced_markers [challenge_duration.days] [obstacle_duration ['value']] = True
                sequenced_obstacles = False
            else:
                sequenced_obstacles = True

            obstacle_set = []

            if sequenced_obstacles:
                for i in range (1, challenge_duration.days // obstacle_duration ['days'] + 1):
                    task = random.choice (tasks)

                    if task.discrete:
                        threshold = Decimal (random.randint (1, 18))
                    else:
                        threshold = Decimal (random.randint (10, 180) / 10)

                    if challenge.category.name == 'Mixed':
                        subcategory = random.choice (subcategories)
                    else:
                        subcategory = None

                    obstacle = Obstacle (
                        challenge=challenge,
                        task=task,
                        interval=obstacle_duration ['value'],
                        sequence_rank=i,
                        threshold=threshold,
                        subcategory=subcategory)

                    obstacle.save ()

                    obstacle_set.append (obstacle)
            else:
                task = random.choice (tasks)

                if task.discrete:
                    threshold = Decimal (random.randint (1, 18))
                else:
                    threshold = Decimal (random.randint (10, 180) / 10)

                obstacle = Obstacle (
                    challenge=challenge,
                    task=task,
                    interval=obstacle_duration ['value'],
                    sequence_rank=None,
                    threshold=threshold,
                    subcategory=None)

                obstacle.save ()

                obstacle_set.append (obstacle)

            challenge.obstacles = obstacle_set
            challenge.save ()
