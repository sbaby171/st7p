import os, sys, re
from collections import OrderedDict
# ============================================================================:
TIMING_LEVEL_SETUP_FILE_KEYWORDS = [
"ADJUST","CHECK","CLKSET","clockSrc","DEFINES","DPSPINS","WAVETBL",
"EQNSET","EQUATIONS","fract","LEVELSET","master_clock","MODECONTEXT",
"MODULATION","PDC","PHYDVCTBL","PINS","PORT","period_div","period_res",
"SPECIFICATION","SPECS","SPECSET","SYNC","TIMINGSET","v3_delay_register_value",
]
# NOTE: See: Timing equation set reference: TDC: 104187
# ============================================================================:
def verify_path(_file,dir=""):
    """ 
    Parameters: 
      file : string
        string with file path. Absolute and relative files supported. 

      dir : string, default = ""
        string used to resolved relative paths. If nothing provide and `file`
        is a relative path, then current-working-directory will be used. 

    Ex.) For a testflow-master-file setup-file reference, the device's 
         testflow directory should be the starting relative path. 
    """
    func = "st7putils.verify_path"
    if not dir: 
        dir = os.getcwd() 
    relative_path_count = _file.count("../")
    afile = os.path.abspath(_file)
    ffile = os.path.join(dir,_file)
    if relative_path_count == 0: 
        if os.path.isfile(_file):   return afile
        elif os.path.isfile(ffile): return ffile
        raise RuntimeError("File `%s` is wrong."%(_file)) 
    sdir = dir.split("/")
    sdir = "/".join(sd[:-relative_path_count])
    fpath = os.path.join(sdir,"/".join(file.split("/")[relative_path_count:]))     
    if os.path.isfile(fpath): return fpath
    raise RuntimeError("File '%s' is wrong'"%(fpath))
# ============================================================================:

def is_valid_spec_name(name): 
    """ 
    This function checks if a (spec) name starts with a 
    timing or level setup file keyword. 
    """
    for kw in TIMING_LEVEL_SETUP_FILE_KEYWORDS: 
        if name.startswith(kw): return False 
    return True


def is_integer(value): 
    """
    This function will check if the input is an integer and return the 
    integer if it is. Note, positive and negative values allowed. Floats or
    doubles are not supported.
    """
    try: 
        _value  = int(value)
        value_int = True
    except: 
        _value = False 
        value_int = False
    return value_int, _value 

     




# ============================================================================:
class Container(object): 
    def __init__(self): 
        self.objects = OrderedDict() 

    def add(self,entity,classtype, overwrite=False):
        if not isinstance(entity,classtype): 
            raise ValueError("Must provide instance of %s. "\
                             "Recieved '%s'"%(classtype,type(entity)))
        if entity.name in self.objects: 
            if not overwrite:
                raise ValueError("Name '%s' was already added."%(entity.name))
            else: 
                print("NOTE: [%s]: '%s' is already registered. "\
                      "Not adding duplicate."%(type(entity),entity.name))
        self.objects[entity.name] = entity
        return 

    def names(self,): 
        x = list(self.object.keys()) 
        x.sort()
        return x

    def contains(self, name): 
        if name not in self.objects.keys(): return False 
        else: return True

    def __contains__(self, name): 
        if name not in self.objects.keys(): return False 
        else: return True

    def names(self):
        return list(self.objects.keys())

    def get(self, name): 
        return self.objects[name]

    def length(self): 
        return len(self.objects)
   
    def __len__(self): 
        return len(self.objects)
 
    def __getitem__(self, name): 
        return self.objects[name]

    def __iter__(self): 
        for name in self.objects.keys(): 
            yield self.objects[name]

    def __last__(self): 
        return self.objects[next(reversed(self.objects))]

# ----------------------------------------------------------------------------:

def _93k_file_handler(sfp, filetype=""): 
    """ 
    This function is to take in a specific 93k file and return the 
    absolute path (abspath), the device-directoy path (ddpath), and the 
    file name (filename); in repsecitve order. 

    Supported file types. Note these are to follow the naming conventions 
    of the subdirectories within a 93k device-directory:  
      - testflow
      - configuration
      - levels
      - timing
      - vectors
    """
    filetypeOpts = ["testflow", "configuration","levels","timing","vectors"]
    if filetype not in filetypeOpts: 
        raise ValueError("Filetype '%s' is not supported. "\
                         "See supported options: %s"%(filetype,filetypeOpts))
    if not os.path.isfile(sfp): 
        raise RuntimeError("Invalid file-path: %s"%(sfp))
    abspath = os.path.abspath(sfp)
    filetype = "/" + filetype + "/"
    if filetype not in abspath: 
        #raise RuntimeError("The sub-directory is not found: %s, %s"%(filetype, abspath))
        print("WARNING: The sub-directory is not found: %s, %s"%(filetype, abspath))
        print("WARNING: Setting `ddpath` to null, `abspath` and `filename` are maintained. ")
        ddpath = None; filename = os.path.basename(sfp)
        return abspath, ddpath, filename 
    ddpath , filename = abspath.split(filetype)
    return abspath, ddpath, filename 



#-----------------------------------------------------------------------------:
#-----------------------------------------------------------------------------:

NUMBER, PLUS, MINUS, MUL, DIV, LPAREN, RPAREN, EOF, VARIABLE = (
    'NUMBER', 'PLUS', 'MINUS', 'MUL', 'DIV', '(', ')', 'EOF',
    'VARIABLE', 
    # 'EXP', 
)

variable_start_char  = re.compile("[_a-zA-Z]")
variable_chars       = re.compile("\w")

class EqToken(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        """String representation of the class instance.

        Examples:
            EqToken(INTEGER, 3)
            EqToken(PLUS, '+')
            EqToken(MUL, '*')
        """
        return 'EqToken({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()


class EqLexer(object):
    def __init__(self, text):
        # client string input, e.g. "4 + 2 * 3 - 6 / 2"
        self.text = text
        # self.pos is an index into self.text
        self.pos = 0
        self.current_char = self.text[self.pos]

    def error(self):
        raise Exception('Invalid character')

    def advance(self):
        """Advance the `pos` pointer and set the `current_char` variable."""
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None  # Indicates end of input
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def number(self):
        """Return a (multidigit) integer consumed from the input."""
        result = ''; is_float = False 
        while self.current_char is not None: 
            
            if self.current_char == ".":
                is_float = True 
                result += self.current_char
                self.advance()
            elif self.current_char.isdigit():
                result += self.current_char
                self.advance()
            else: break 
        
        if is_float: 
            return float(result)
        return int(result)
    
    def variable(self):
        """Return a (multidigit) integer consumed from the input."""
        result = ''; is_float = False 
        while self.current_char is not None: 
            
            if variable_chars.search(self.current_char):
                result += self.current_char
                self.advance()
            else: break 
        return result

    def get_next_token(self):
        """Lexical analyzer (also known as scanner or tokenizer)

        This method is responsible for breaking a sentence
        apart into tokens. One token at a time.
        """
        while self.current_char is not None:

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                return EqToken(NUMBER, self.number())
            
            if variable_start_char.search(self.current_char): 
                return EqToken(VARIABLE, self.variable())

            if self.current_char == '+':
                self.advance()
                return EqToken(PLUS, '+')

            if self.current_char == '-':
                self.advance()
                return EqToken(MINUS, '-')

            if self.current_char == '*':
                self.advance()
                return EqToken(MUL, '*')

            if self.current_char == '/':
                self.advance()
                return EqToken(DIV, '/')

            if self.current_char == '(':
                self.advance()
                return EqToken(LPAREN, '(')

            if self.current_char == ')':
                self.advance()
                return EqToken(RPAREN, ')')

            self.error()

        return EqToken(EOF, None)



class AST(object):
    pass


class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right


class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value
        
# TODO: I think we need another class here: Var(AST)
class Var(AST): 
    def __init__(self,token): 
        self.token = token 
        self.value = token.value


class EqParser(object):
    def __init__(self, lexer):
        self.lexer = lexer
        # set current token to the first token taken from the input
        self.current_token = self.lexer.get_next_token()
        self.last_token = None # MS: for 'look-back' capability

    def error(self):
        raise Exception('Invalid syntax')

    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        if self.current_token.type == token_type:
            self.last_token = self.current_token 
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def factor(self):
        """factor : INTEGER | LPAREN expr RPAREN"""
        func = "%s.factor"%(self.__class__.__name__)
        token = self.current_token
        if token.type == NUMBER:
            self.eat(NUMBER)
            return Num(token)
        
        elif token.type == VARIABLE:  # NEW
            self.eat(VARIABLE)
            return Var(token)
        
        elif token.type == LPAREN:            
            self.eat(LPAREN)
            node = self.expr()
            self.eat(RPAREN)
            return node
        else: self.error()

    def term(self):
        """term : factor ((MUL | DIV) factor)*"""
        func = "%s.term"%(self.__class__.__name__)
        
        node = self.factor()
        while self.current_token.type in (MUL, DIV):
            token = self.current_token
            if token.type == MUL:
                self.eat(MUL)
            elif token.type == DIV:
                self.eat(DIV)

            node = BinOp(left=node, op=token, right=self.factor())

        return node

    def expr(self):
        """
        expr   : term ((PLUS | MINUS) term)*
        term   : factor ((MUL | DIV) factor)*
        factor : INTEGER | LPAREN expr RPAREN
        """
        node = self.term()

        while self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            if token.type == PLUS:
                self.eat(PLUS)
            elif token.type == MINUS:
                self.eat(MINUS)

            node = BinOp(left=node, op=token, right=self.term())

        return node

    def parse(self):
        return self.expr()


###############################################################################
#                                                                             #
#  INTERPRETER                                                                #
#                                                                             #
###############################################################################

class NodeVisitor(object):
    def visit(self, node, total_vars):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, total_vars)

    def generic_visit(self, node, total_vars):
        raise Exception('No visit_{} method'.format(type(node).__name__))

class EqInterpreter(NodeVisitor):
    def __init__(self, parser):
        self.parser = parser
        # TODO: pass in total_vars because we create a new instance for each equation

    def visit_BinOp(self, node, total_vars):
                    
        if isinstance(node.left,Var):
            #print("Left Node is Var: %s"%(node.left.value))
            #print("  %s: %s"%(node.left.value, total_vars[node.left.value]))
            node.left = Num(EqToken(NUMBER, total_vars[node.left.value]))
                
        if isinstance(node.right,Var):
            #print("Right Node is Var: %s"%(node.right.value))
            #print(total_vars.items())
            #print("  %s: %s"%(node.right.value, total_vars[node.right.value]))
            node.right = Num(EqToken(NUMBER, total_vars[node.right.value]))
        
        
        if node.op.type == PLUS:
            return self.visit(node.left, total_vars) + self.visit(node.right, total_vars)
        elif node.op.type == MINUS:
            return self.visit(node.left, total_vars) - self.visit(node.right, total_vars)
        elif node.op.type == MUL:
            return self.visit(node.left, total_vars) * self.visit(node.right, total_vars)
        elif node.op.type == DIV:
            return self.visit(node.left, total_vars) / self.visit(node.right, total_vars)

    def visit_Num(self, node, total_vars):
        return node.value

    def interpret(self, total_vars):
        tree = self.parser.parse()
        return self.visit(tree, total_vars)


def compute(expr,total_vars,debug=False):
    if debug: print("DEBUG: (st7putil.compute): Computing expression: %s"%(expr)) 
    changed = False; backup=expr
    while True: 
        if expr == "-VDD_075 /2": expr = "(0.0 - VDD_075)/2"; changed=True; break
        if expr == ".4": expr = "0.4"; changed = True; break
        if expr == ".3": expr = "0.3"; changed = True; break
        if expr == ".42": expr = "0.42"; changed = True; break
        if expr == ".56": expr = "0.56"; changed = True; break
        if expr == "VDD_18*.65": expr = "VDD_18 * 0.65"; changed=True; break
        if expr == "VDD_18*.35": expr = "VDD_18 * 0.35"; changed=True; break
        break
   
    if changed: 
        print("(st7putil.compute): Changed expression: %s"%(backup)) 
        print("(st7putil.compute):     new expression: %s"%(expr)) 


    lexer = EqLexer(expr)
    parser = EqParser(lexer)
    interpreter = EqInterpreter(parser)
    result = interpreter.interpret(total_vars) 
    return result


