from flask import Flask, render_template, request, jsonify
from lark import Lark, Transformer, Tree
import math
import re  # Para dividir correctamente la expresión en tokens

app = Flask(__name__)

# Gramática de la calculadora
grammar = """
    ?start: expr
    ?expr: expr "+" term   -> add
         | expr "-" term   -> sub
         | term
    ?term: term "*" factor -> mul
         | term "/" factor -> div
         | factor
    ?factor: factor "^" atom -> pow
           | atom
    ?atom: "-" atom          -> neg
         | "sqrt(" expr ")"  -> sqrt
         | "abs(" expr ")"   -> abs
         | "cos(" expr ")"   -> cos
         | "cot(" expr ")"   -> cot
         | "(" expr ")"
         | NUMBER            -> number

    %import common.NUMBER
    %import common.WS
    %ignore WS
"""

# Transformador para procesar el árbol de análisis
class CalculateTree(Transformer):
    def add(self, args):
        return args[0] + args[1]

    def sub(self, args):
        return args[0] - args[1]

    def mul(self, args):
        return args[0] * args[1]

    def div(self, args):
        return args[0] / args[1]

    def neg(self, args):
        return -args[0]

    def sqrt(self, args):
        return math.sqrt(args[0])

    def abs(self, args):
        return abs(args[0])

    def cos(self, args):
        return math.cos(math.radians(args[0]))

    def cot(self, args):
        return 1 / math.tan(math.radians(args[0])) if math.tan(math.radians(args[0])) != 0 else float('inf')

    def pow(self, args):
        return args[0] ** args[1]

    def number(self, args):
        return float(args[0])

# Crear el parser con la gramática
parser = Lark(grammar, parser='lalr', transformer=CalculateTree())

# Convertir el árbol de análisis a un formato JSON jerárquico
def generate_tree_json(tree):
    translations = {
        "add": "suma",
        "sub": "resta",
        "mul": "multiplicación",
        "div": "división",
        "neg": "negativo",
        "sqrt": "raíz cuadrada",
        "abs": "valor absoluto",
        "cos": "coseno",
        "cot": "cotangente",
        "pow": "potencia",
        "number": "número"
    }
    if isinstance(tree, Tree):
        return {
            "name": translations.get(tree.data, tree.data),
            "children": [generate_tree_json(child) for child in tree.children]
        }
    else:
        return {"name": str(tree)}

# Función para analizar tokens
def analyze_tokens(expression):
    token_regex = re.compile(r'\d+\.\d+|\d+|[+\-*/^()]|sqrt|abs|cos|cot')
    matches = token_regex.findall(expression)

    tokens = []
    total_numbers = 0
    total_integers = 0
    total_decimals = 0
    total_operators = 0

    for match in matches:
        if match.replace('.', '', 1).isdigit():
            total_numbers += 1
            if '.' in match:
                total_decimals += 1
                tokens.append({"tipo": "Decimal", "valor": match})
            else:
                total_integers += 1
                tokens.append({"tipo": "Entero", "valor": match})
        elif match in "+-*/^":
            total_operators += 1
            tokens.append({"tipo": "Operador", "valor": match})
        else:
            tokens.append({"tipo": "Función", "valor": match})

    return tokens, total_numbers, total_integers, total_decimals, total_operators

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        expression = request.json.get('expression', '').strip()
        try:
            # Analizar y calcular
            parse_tree = Lark(grammar, parser='lalr').parse(expression)
            result = parser.parse(expression)

            # Convertir árbol a JSON
            tree_json = generate_tree_json(parse_tree)

            # Analizar tokens
            tokens, total_numbers, total_integers, total_decimals, total_operators = analyze_tokens(expression)

            return jsonify({
                "result": result,
                "tokens": tokens,
                "total_tokens": len(tokens),
                "total_numeros": total_numbers,
                "total_enteros": total_integers,
                "total_decimales": total_decimals,
                "total_operadores": total_operators,
                "tree_json": tree_json
            })
        except Exception as e:
            return jsonify({"error": f"Expresión inválida: {str(e)}"}), 400
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
