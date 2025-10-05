from django.core.management.base import BaseCommand
from exercises.models import MuscleGroup, Exercise


class Command(BaseCommand):
    help = 'Populate the database with exercise data'

    def handle(self, *args, **options):
        self.stdout.write('Creating muscle groups...')
        
        # Create muscle groups
        muscle_groups_data = [
            ('Chest', 'Pectoral muscles'),
            ('Back', 'Latissimus dorsi, rhomboids, and middle trapezius'),
            ('Shoulders', 'Deltoids and rotator cuff muscles'),
            ('Arms', 'Biceps and triceps'),
            ('Legs', 'Quadriceps, hamstrings, and glutes'),
            ('Core', 'Abdominals and obliques'),
            ('Calves', 'Gastrocnemius and soleus'),
            ('Forearms', 'Forearm flexors and extensors'),
        ]
        
        muscle_groups = {}
        for name, description in muscle_groups_data:
            mg, created = MuscleGroup.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            muscle_groups[name] = mg
            if created:
                self.stdout.write(f'Created muscle group: {name}')

        self.stdout.write('Creating exercises...')

        # Exercise data: (name, muscle_groups, description, instructions, difficulty, equipment)
        exercises_data = [
            # Chest exercises
            ('Push-ups', ['Chest', 'Arms'], 
             'Basic bodyweight chest exercise', 
             'Start in plank position, lower body until chest nearly touches ground, push back up',
             'beginner', 'None'),
            ('Bench Press', ['Chest', 'Arms', 'Shoulders'], 
             'Classic barbell chest exercise', 
             'Lie on bench, grip barbell wider than shoulders, lower to chest, press up',
             'intermediate', 'Barbell, Bench'),
            ('Dumbbell Chest Press', ['Chest', 'Arms'], 
             'Dumbbell variation of bench press', 
             'Lie on bench with dumbbells, press up and together',
             'beginner', 'Dumbbells, Bench'),
            ('Chest Flyes', ['Chest'], 
             'Isolation exercise for chest', 
             'Lie on bench, open arms wide with dumbbells, bring together above chest',
             'intermediate', 'Dumbbells, Bench'),
            ('Dips', ['Chest', 'Arms'], 
             'Bodyweight exercise for chest and triceps', 
             'Support body on parallel bars, lower until shoulders below elbows, push up',
             'intermediate', 'Parallel bars or dip station'),

            # Back exercises
            ('Pull-ups', ['Back', 'Arms'], 
             'Bodyweight back exercise', 
             'Hang from bar with palms away, pull up until chin over bar',
             'intermediate', 'Pull-up bar'),
            ('Lat Pulldowns', ['Back', 'Arms'], 
             'Machine exercise for lats', 
             'Sit at machine, pull bar down to chest with wide grip',
             'beginner', 'Lat pulldown machine'),
            ('Deadlifts', ['Back', 'Legs'], 
             'Compound exercise for posterior chain', 
             'Stand with feet hip-width, grip bar, lift by extending hips and knees',
             'intermediate', 'Barbell'),
            ('Barbell Rows', ['Back', 'Arms'], 
             'Bent-over rowing exercise', 
             'Bend at hips, row barbell to lower chest/upper abdomen',
             'intermediate', 'Barbell'),
            ('Dumbbell Rows', ['Back', 'Arms'], 
             'Single-arm rowing exercise', 
             'Support one knee on bench, row dumbbell to side',
             'beginner', 'Dumbbell, Bench'),
            ('T-Bar Rows', ['Back', 'Arms'], 
             'Machine rowing exercise', 
             'Bend at hips, pull T-bar to chest',
             'intermediate', 'T-bar row machine'),

            # Shoulder exercises
            ('Overhead Press', ['Shoulders', 'Arms'], 
             'Standing shoulder press', 
             'Stand with feet hip-width, press weight overhead',
             'intermediate', 'Barbell or dumbbells'),
            ('Lateral Raises', ['Shoulders'], 
             'Side deltoid isolation', 
             'Hold dumbbells at sides, raise out to shoulder height',
             'beginner', 'Dumbbells'),
            ('Front Raises', ['Shoulders'], 
             'Front deltoid isolation', 
             'Hold dumbbells in front, raise to shoulder height',
             'beginner', 'Dumbbells'),
            ('Rear Delt Flyes', ['Shoulders'], 
             'Rear deltoid isolation', 
             'Bend forward, raise dumbbells out to sides',
             'beginner', 'Dumbbells'),
            ('Shrugs', ['Shoulders', 'Back'], 
             'Trapezius exercise', 
             'Hold weights at sides, lift shoulders toward ears',
             'beginner', 'Dumbbells or barbell'),

            # Arms exercises
            ('Bicep Curls', ['Arms'], 
             'Basic bicep exercise', 
             'Hold weights with arms extended, curl up by flexing biceps',
             'beginner', 'Dumbbells or barbell'),
            ('Hammer Curls', ['Arms', 'Forearms'], 
             'Neutral grip bicep exercise', 
             'Hold dumbbells with neutral grip, curl up',
             'beginner', 'Dumbbells'),
            ('Tricep Extensions', ['Arms'], 
             'Overhead tricep exercise', 
             'Hold weight overhead, lower behind head, extend back up',
             'beginner', 'Dumbbell'),
            ('Tricep Dips', ['Arms'], 
             'Bodyweight tricep exercise', 
             'Sit on edge of bench, lower body with arms, push back up',
             'beginner', 'Bench or chair'),
            ('Close-Grip Push-ups', ['Arms', 'Chest'], 
             'Tricep-focused push-up variation', 
             'Push-up with hands close together under chest',
             'intermediate', 'None'),

            # Leg exercises
            ('Squats', ['Legs'], 
             'Fundamental leg exercise', 
             'Stand with feet shoulder-width, squat down, stand back up',
             'beginner', 'None or barbell'),
            ('Lunges', ['Legs'], 
             'Single-leg strength exercise', 
             'Step forward into lunge position, push back to start',
             'beginner', 'None or dumbbells'),
            ('Leg Press', ['Legs'], 
             'Machine leg exercise', 
             'Sit in machine, press weight with legs',
             'beginner', 'Leg press machine'),
            ('Romanian Deadlifts', ['Legs', 'Back'], 
             'Hip hinge movement', 
             'Hold barbell, hinge at hips keeping legs relatively straight',
             'intermediate', 'Barbell'),
            ('Leg Curls', ['Legs'], 
             'Hamstring isolation', 
             'Lie prone, curl legs up against resistance',
             'beginner', 'Leg curl machine'),
            ('Leg Extensions', ['Legs'], 
             'Quadriceps isolation', 
             'Sit in machine, extend legs against resistance',
             'beginner', 'Leg extension machine'),
            ('Wall Sits', ['Legs'], 
             'Isometric leg exercise', 
             'Lean back against wall in squat position, hold',
             'beginner', 'Wall'),

            # Core exercises
            ('Planks', ['Core'], 
             'Isometric core exercise', 
             'Hold push-up position with straight body',
             'beginner', 'None'),
            ('Crunches', ['Core'], 
             'Basic abdominal exercise', 
             'Lie on back, curl torso up toward knees',
             'beginner', 'None'),
            ('Russian Twists', ['Core'], 
             'Rotational core exercise', 
             'Sit with knees bent, rotate torso side to side',
             'beginner', 'None or medicine ball'),
            ('Mountain Climbers', ['Core', 'Legs'], 
             'Dynamic core exercise', 
             'Start in plank, alternate bringing knees to chest quickly',
             'intermediate', 'None'),
            ('Dead Bug', ['Core'], 
             'Core stability exercise', 
             'Lie on back, extend opposite arm and leg, return to start',
             'beginner', 'None'),
            ('Bicycle Crunches', ['Core'], 
             'Dynamic ab exercise', 
             'Lie on back, alternate bringing elbow to opposite knee',
             'beginner', 'None'),

            # Calf exercises
            ('Calf Raises', ['Calves'], 
             'Standing calf exercise', 
             'Stand on balls of feet, raise up on toes, lower slowly',
             'beginner', 'None or dumbbells'),
            ('Seated Calf Raises', ['Calves'], 
             'Seated calf variation', 
             'Sit with weight on thighs, raise up on toes',
             'beginner', 'Dumbbells or machine'),
        ]

        for name, muscle_group_names, description, instructions, difficulty, equipment in exercises_data:
            exercise, created = Exercise.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'instructions': instructions,
                    'difficulty': difficulty,
                    'equipment_needed': equipment,
                }
            )
            
            if created:
                # Add muscle groups
                for mg_name in muscle_group_names:
                    exercise.muscle_groups.add(muscle_groups[mg_name])
                self.stdout.write(f'Created exercise: {name}')
            else:
                self.stdout.write(f'Exercise already exists: {name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated database with {len(exercises_data)} exercises and {len(muscle_groups_data)} muscle groups'
            )
        )