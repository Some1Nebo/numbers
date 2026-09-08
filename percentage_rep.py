"""Percentage reasoning with controlled operands and explicit decimal rounding."""

from decimal import Decimal, ROUND_HALF_UP
import random
import re


KINDS = ('of', 'increase', 'decrease', 'ratio', 'reverse_increase', 'reverse_decrease')
CENT = Decimal('0.01')


def number_text(value):
    return format(value, 'f').rstrip('0').rstrip('.') if '.' in format(value, 'f') else format(value, 'f')


class PercentageRep:
    def __init__(self, kind, value, rate):
        self.kind = kind
        self.value, self.rate = Decimal(str(value)), Decimal(str(rate))
        if kind not in KINDS or not all(v.is_finite() and v > 0 for v in (self.value, self.rate)):
            raise ValueError('A percentage exercise needs a known kind and positive finite operands.')
        if kind in ('decrease', 'reverse_decrease') and self.rate >= 100:
            raise ValueError('A decrease must be less than 100%.')

    def _exact_answer(self):
        factor = self.rate / 100
        if self.kind == 'of':
            return self.value * factor
        if self.kind == 'ratio':
            return self.value / self.rate * 100
        if self.kind == 'increase':
            return self.value * (1 + factor)
        if self.kind == 'decrease':
            return self.value * (1 - factor)
        if self.kind == 'reverse_increase':
            return self.value / (1 + factor)
        return self.value / (1 - factor)

    def answer(self):
        return self._exact_answer().quantize(CENT, rounding=ROUND_HALF_UP)

    @property
    def answer_text(self):
        return number_text(self.answer()) + ('%' if self.kind == 'ratio' else '')

    @property
    def display(self):
        value, rate = number_text(self.value), number_text(self.rate)
        if self.kind == 'of':
            return f'{rate}% of {value}'
        if self.kind == 'ratio':
            return f'{value} is what percentage of {rate}?'
        if self.kind in ('increase', 'decrease'):
            return f'{self.kind.capitalize()} {value} by {rate}%'
        change = 'increase' if self.kind == 'reverse_increase' else 'decrease'
        return f'After a {rate}% {change}, the value is {value}. What was it before?'

    @property
    def instruction(self):
        rounded = self._exact_answer() != self.answer()
        precision = 'Round to two decimal places (5 rounds up).' if rounded else 'Enter a number; decimals are welcome.'
        if self.kind == 'ratio':
            precision = 'Answer as a percentage. ' + precision
        return precision

    @property
    def input_error(self):
        return 'Enter a number, such as 12 or 12.5.' + (' A % sign is optional.' if self.kind == 'ratio' else '')

    def parse_answer(self, answer):
        if not isinstance(answer, str):
            raise ValueError(self.input_error)
        text = answer.strip().replace('−', '-')
        if self.kind == 'ratio' and text.endswith('%'):
            text = text[:-1].strip()
        if len(text) > 40 or not re.fullmatch(r'[+-]?(?:[0-9]+(?:[.,][0-9]*)?|[.,][0-9]+)', text):
            raise ValueError(self.input_error)
        return Decimal(text.replace(',', '.'))

    def matches_answer(self, answer):
        parsed = self.parse_answer(answer)
        # Bound before quantizing so even an enormous valid input is simply wrong.
        if abs(parsed - self.answer()) > 1:
            return False
        if self._exact_answer() == self.answer():
            return parsed == self.answer()
        return parsed.quantize(CENT, rounding=ROUND_HALF_UP) == self.answer()

    def __str__(self):
        # Saved and console prompts include the answer convention.
        return f'{self.display} ({self.instruction})'

    @staticmethod
    def generate(mode):
        if mode not in ('s', 'm', 'h'):
            raise ValueError('Unknown difficulty.')
        rates = {'s': ('1', '5', '10', '20', '25', '50'),
                 'm': ('12.5', '15', '25', '30', '35', '40', '60', '75'),
                 'h': ('7', '12.5', '17', '22', '35', '65')}[mode]
        kind = random.choice(KINDS if mode == 'h' else KINDS[:4])
        rate = Decimal(random.choice(rates))
        base = Decimal(random.randint(1, 8) * (100 if mode == 's' else 20))
        if kind == 'ratio':
            return PercentageRep(kind, base * rate / 100, base)
        if kind.startswith('reverse'):
            # Work backwards from a tidy original to make reasoning the challenge.
            factor = 1 + rate / 100 if kind == 'reverse_increase' else 1 - rate / 100
            return PercentageRep(kind, base * factor, rate)
        if mode == 'h':
            base = Decimal(random.randint(20, 200))
        return PercentageRep(kind, base, rate)
