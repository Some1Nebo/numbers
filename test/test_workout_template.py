import unittest
from workout_template import *


class WorkoutTemplateParseTests(unittest.TestCase):

    def test_happy_path(self):
        template = WorkoutTemplate.parse("s-a,m-10")

        self.assertEquals(template.mode(), Mode.SIMPLE)
        self.assertEquals(template.rep_types(), {RepType.ADDITION,
                                                 RepType.MULTIPLICATION})
        self.assertEquals(template.num_of_reps(), 10)

    def test_valid_format_with_wild_card(self):
        template = WorkoutTemplate.parse("s-a,*-10")

        self.assertEquals(template.mode(), Mode.SIMPLE)
        self.assertEquals(template.rep_types(), {RepType.ADDITION,
                                                 RepType.MULTIPLICATION,
                                                 RepType.DIVISION,
                                                 RepType.SUBTRACTION})
        self.assertEquals(template.num_of_reps(), 10)

    def test_throws_if_wrong_format(self):
        self.assertRaises(ValueError, WorkoutTemplate.parse, "s-a,m:10")
        self.assertRaises(ValueError, WorkoutTemplate.parse, "s-a,m")
        self.assertRaises(ValueError, WorkoutTemplate.parse, "s,s-a,m-10")

    def test_throws_if_unknown_template_values(self):
        self.assertRaises(ValueError, WorkoutTemplate.parse, "s-x,m-10")
        self.assertRaises(ValueError, WorkoutTemplate.parse, "x-a,m-10")

    def test_throws_if_not_integer_for_num_of_reps(self):
        self.assertRaises(ValueError, WorkoutTemplate.parse, "s-a,m-not_int")
        self.assertRaises(ValueError, WorkoutTemplate.parse, "s-a,m-10~")


if __name__ == "__main__":
    unittest.main()
