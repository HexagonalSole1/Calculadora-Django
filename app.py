from flask import Flask, render_template, request, jsonify
from lark import Lark, Transformer, Tree
import ply.lex as lex

app = Flask(__name__)

# Configuración de gramática
grammar = """
    ?start: expr
    ?expr: expr "+" term   -> add
         | expr "-" term   -> sub
         | term
    ?term: term "*" factor  -> mul
         | term "/" factor  -> div
         | factor
    ?factor: "(" expr ")"
           | NUMBER           -> number

    %import common.NUMBER
    %import common.WS
    %ignore WS
"""

class CalculateTree(Transformer):
    def add(self, args):
        return args[0] + args[1]
    def sub(self, args):
        return args[0] - args[1]
    def mul(self, args):
        return args[0] * args[1]
    def div(self, args):
        return args[0] / args[1]
    def number(self, args):
        return float(args[0])

parser = Lark(grammar, parser='lalr', transformer=CalculateTree())

# Definición de tokens
tokens = (
    'NUMERO',
    'SUMA',
    'RESTA',
    'MULTIPLICACION',
    'DIVISION',
    'LPAREN',
    'RPAREN'
)

t_SUMA = r'\+'
t_RESTA = r'-'
t_MULTIPLICACION = r'\*'
t_DIVISION = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'

def t_NUMERO(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

t_ignore = ' \t'

def t_error(t):
    raise ValueError(f"Token inválido: {t.value[0]}")

lexer = lex.lex()

def analyze_tokens(expression):
    lexer.input(expression)
    tokens_list = []
    total_numbers = 0
    total_operators = 0
    total_integers = 0
    total_decimals = 0

    for token in lexer:
        tokens_list.append(token)
        if token.type == 'NUMERO':
            total_numbers += 1
            if isinstance(token.value, int):
                total_integers += 1
            else:
                total_decimals += 1
        elif token.type in {'SUMA', 'RESTA', 'MULTIPLICACION', 'DIVISION'}:
            total_operators += 1

    return tokens_list, total_numbers, total_operators, total_integers, total_decimals

def generate_html_tree(tree):
    def build_html(tree):
        if isinstance(tree, Tree):
            children = "".join([build_html(child) for child in tree.children])
            return f"<li>{tree.data}<ul>{children}</ul></li>"
        else:
            return f"<li>{tree}</li>"

    return f"<ul>{build_html(tree)}</ul>"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        expression = request.json.get('expression')
        try:
            tokens_list, total_numbers, total_operators, total_integers, total_decimals = analyze_tokens(expression)
            parse_tree = Lark(grammar, parser='lalr').parse(expression)
            result = parser.parse(expression)
            tree_html = generate_html_tree(parse_tree)

            # Guardar en archivo de texto
            with open("resultados.txt", "a") as f:
                f.write(f"Expresión: {expression}, Resultado: {result}\n")

            return jsonify({
                "result": result,
                "tokens": [{"tipo": t.type, "valor": t.value} for t in tokens_list],
                "total_tokens": total_numbers + total_operators,
                "total_numeros": total_numbers,
                "total_enteros": total_integers,
                "total_decimales": total_decimals,
                "total_operadores": total_operators,
                "tree_html": tree_html
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
