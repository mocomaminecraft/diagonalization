import math
from functools import reduce

class Term:
    def __init__(self, coefficient, degree):
        self.coefficient = coefficient
        self.degree = degree

    @classmethod
    def numerical(cls, num):
        return cls(num, 0)

    def derivate(self):
        return Term(self.coefficient * self.degree, self.degree - 1)

    def evaluate(self, value):
        return self.coefficient * value ** self.degree

    def is_numerical(self):
        return self.degree == 0

    def __str__(self):
        if self.is_numerical(): return str(self.coefficient)
        elif self.degree == 1: return f"{self.coefficient}x"
        else: return f"{self.coefficient}x^{self.degree}"

    def __radd__(self, other):
        return self + other

    def __add__(self, other):
        if not isinstance(other, Term):
            other = Term.numerical(other)
        
        if math.isclose(self.degree, other.degree):
            return Term(self.coefficient + other.coefficient, self.degree)
        else:
            return Poly([self, other])

    def __rsub__(self, other):
        return self - other

    def __sub__(self, other):
        return self + (other * -1)

    def __rmul__(self, other):
        return self * other

    def __mul__(self, other):
        if not isinstance(other, Term):
            other = Term.numerical(other)

        return Term(self.coefficient * other.coefficient, self.degree + other.degree)

    def __truediv__(self, other):
        if not isinstance(other, Term):
            other = Term.numerical(other)

        return Term(self.coefficient / other.coefficient, self.degree - other.degree)

class Poly:
    def __init__(self, terms=None):
        self.terms = terms if terms is not None else []

    @classmethod
    def from_str(cls, string):
        poly = cls()
        for term in string.split(" + "):
            if "x" not in term:
                poly += Term.numerical(float(term))
            else:
                coefficient, degree = term.split("x")
                poly += Term(
                        float(coefficient if coefficient else 1),
                        int(degree[1:]) if degree else 1
                        )

        return poly

    @classmethod
    def copy(cls, other):
        return cls([term for term in other.terms])

    def get_degrees(self):
        return [term.degree for term in self.terms]

    def get_degree(self):
        return max(self.get_degrees())

    def get_coefficients(self):
        return [term.coefficient for term in self.terms]

    def get_leading_coefficient(self):
        max_deg = self.get_degree()
        for term in self.terms:
            if term.degree == max_deg:
                return term.coefficient

    def has_degree(self, degree):
        return degree in (term.degree for term in self.terms)

    def derivate(self):
        new = Poly()
        for term in self.terms:
            new += term.derivate()

        new.purge()
        return new

    def evaluate(self, value):
        result = 0
        for term in self.terms:
            result += term.evaluate(value)

        return result

    def all_terms(self):
        result = Poly.copy(self)
        
        n = self.get_degree()
        degrees = [term.degree for term in self.terms]
        for i in range(n):
            if i not in degrees:
                result.terms.append(Term(0, i))

        return result

    def purge(self):
        self.terms = [term for term in self.terms if term.coefficient != 0]

    def __str__(self):
        return " + ".join(str(term) for term in
                sorted(self.terms, key=lambda term: term.degree, reverse=True)
                )

    def __iadd__(self, other):
        self = self + other
        return self

    def __radd__(self, other):
        return self + other

    def __add__(self, other):
        if isinstance(other, Term):
            if self.has_degree(other.degree):
                result = Poly()
                for term in self.terms:
                    if math.isclose(term.degree, other.degree):
                        term += other

                    result += term

                return result
            else:
                return Poly(self.terms + [other])

        elif isinstance(other, Poly):
            new = Poly()
            for term in self.terms:
                new += term
            
            for term in other.terms:
                new += term

            return new

        else:
            return self + Term.numerical(other)

    def __isub__(self, other):
        self = self - other
        return self

    def __rsub__(self, other):
        return self - other

    def __sub__(self, other):
        return self + (other * -1)

    def __rmul__(self, other):
        return self * other

    def __mul__(self, other):
        if isinstance(other, Poly):
            result = Poly()
            for term in self.terms:
                result += other * term

            return result
        else:
            return Poly([term * other for term in self.terms])

    def __itruediv__(self, other):
        self = self / other
        return self

    def __truediv__(self, other):
        result = Poly.copy(self)
        result.terms = [term/other for term in self.terms]
        return result

    def __eq__(self, other):
        return all(term1 == term2 for term1, term2 in zip(
            sorted(self.terms, key=lambda term: term.degree),
            sorted(self.terms, key=lambda term: term.degree)
        ))

def square_free(poly):
    """Removes double roots of a polynomial, by dividing by x^2 as much as it can
    """
    all_divisible = True
    while True: 
        for term in poly.terms:
            if term.degree % 2 != 0:
                all_divisible = False

        if all_divisible:
            poly = Poly([Term(term.coefficient, term.degree / 2) for term in poly.terms])
        else:
            break

    return poly

def calc_roots(poly_in, epsilon=1e-12):
    """Calculates an aproximation of the roots of a polynomial, using the 
    Durand-Kerner method
    """

    #Make the polynomial so its leading coefficient is 0
    poly = poly_in / poly_in.get_leading_coefficient()

    def calc_next(prev, prev_aprox):
        #The formula to calculate the next aproximation of a coefficient from
        #having the aproximations of the others
        return prev - poly.evaluate(prev)/reduce(lambda acc, n: acc * n, (prev - other for other in prev_aprox), 1)

    def aproximate(num):
        real, imag = num.real, num.imag

        if abs(real) < epsilon: real = 0
        else: real = round(real)

        if abs(imag) < epsilon: imag = 0
        else: imag = round(imag)

        #Choose the best of all options
        possible = [complex(real, imag), complex(num.real, imag), complex(real, num.imag), complex(real, imag), num]
        best = min(possible, key=lambda n: abs(poly.evaluate(n)))
        
        #If the best num is only real, dont return a complex number
        if best.imag == 0: 
            #If is an integer, return such
            if best.real % 1 == 0: return int(best.real)
            return best.real
        return best

    #Obtain the first "aproximations" that are simply random complex numbers other than 1, and
    #the first aproximations obtained from those
    prevs = [complex(0.4, 0.9)**n for n in range(poly.get_degree())]
    currs = [calc_next(aprox, [p for p in prevs if p != aprox]) for i,aprox in enumerate(prevs)]
    while max(abs(p - c) for p,c in zip(prevs, currs)) >= 1e-12:
        prevs = currs
        currs = [calc_next(aprox, [p for p in prevs if p != aprox]) for aprox in prevs]

    #Purge negligible values, also return in a predictable way
    return sorted([aproximate(num) for num in currs], reverse=True)
