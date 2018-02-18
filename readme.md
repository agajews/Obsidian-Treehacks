## What the heck is generative programming anyway?
The idea behind generative programming is that rather than writing a program in one language and having it either interpreted and executed directly or compiled to a binary and then executed, we write a program in a host programming language that outputs a source file in a target language. This might seem strange at first; what's the point, you might ask? The advantages are twofold. 

First, we can eliminate repetitive parts of our program by abstracting their generation in the host language. Suppose we have a sparse matrix that's fixed at compile-time and we want to multiply it by another matrix that's provided at runtime. One efficient way to do this is to unroll the loops for rows of the fixed matrix that are more sparse; however, doing that by hand would be tedious and would need to be redone if the compile-time matrix changed. Instead, if we build this program programmatically, we can avoid the manual labor and fine-tune performance much more efficiently. Now, you might say this can be accomplished with macros just as effectively, and you would be right, for the most part. If you're constrained to using C or C++ or CUDA, say because of library dependencies, you don't have macros to work with (decent ones anyway). Generative programming gives metaprogramming capabilities to languages that don't support it natively. 

The second advantage is that because we have access to the full semantic model of our program at compile-time, we can verify the correctness of our program in the same language as we're writing it. We can even do so as we build our program up from expressions. Suppose we're writing a websocket library and we want to ensure that websockets are initialized exactly once before they're opened. This could be accomplished using dependent types in a language like Idris, but first of all Idris is much too cumbersome to use for practical tasks at the moment, and second, if as before we have library dependency constraints, we aren't at liberty to choose a target language at all. Generative programming gives an alternative to dependent types that's more flexible and intuitive.

## Why a new programming language?
Of course, there are excellent generative programming libraries available for other language. One notable example is Scala's LMS library, which is an extremely powerful generative programming library that can target a number of languages including CUDA and C. However, generative programming in Scala is less than streamlined. The sample snipped from the LMS webpage is this:

```scala
class Vector[T:Numeric:Manifest](val data: Rep[Array[T]]) {
  def foreach(f: Rep[T] => Rep[Unit]): Rep[Unit] =
    for (i <- 0 until data.length) f(data(i))
  def sumIf(f: Rep[T] => Rep[Boolean]) = { 
    var n = zero[T]; foreach(x => if (f(x)) n += x); n }
}
```

Not exactly the cleanest code in the world. Obsidian solves this with metaprogramming. In Obsidian, a generative programming library might let the same code might be written as:

```
class vector(data)
    def foreach(f)
        for j in 0..data.length
            f(data(j))

    def sumif(f)
        n = 0
        foreach(x => if f(x) n += x)
        n
```

## What it does
Obsidian lets users define new keywords, essentially multiline macros with minimal boilerplate syntax, which means we can have a separate keyword for Obsidian functions and for functions that represent a chunk of code in the target language. Keywords also receive a raw lexeme stream, which means that they have the liberty to use their own syntax entirely; if a generative programming library designer wished, they could even come close to closely imitating the syntax of the target language!

## Challenges I ran into
I spent about two hours this morning finding a bug in the parser generator library I used, TatSu, that prevented the `#` symbol from being consumed by the lexer. I'll probably have to submit a pull request so that users of Obsidian don't have to manually fix TatSu before they can run the interpreter.

## What's next for Obsidian
So far, I've only made the interpreter for the language. The next step will be to write the first generative programming library and demonstrate the power of keyword definition and dynamic syntax.

## What does Obsidian look like
*Apologies for the lack of syntax highlighting, for obvious reasons*
```
#[
this is a multiline comment
]#

# this is a single line comment

x = 3  # this is an int literal
y = 3.0  # this is a float literal

hello = "world"  # this is a string
h = 'w'  # this is a char

list = [1, 2, h, "orld"]  # this is a list; lists are heterogeneous and represented as linked lists

a = ~blue  # this is a symbol; symbols are represented internally as integers
dict = {~red: "fish", a: ~fish}  # this is a dictionary; the first key is the symbol ~red, and the second is the symbol ~blue

# suppose library has three exported attributes, x, y, and z
import library  # accessible as library.x, library.y, library.z
import library as L  # accessible as L.x, L.y, L.z
import library showing x  # we have x in scope, but need to use library.y and library.z for the others
import library as L showing x  # we have x, L.y, and L.z
using library  # accessible as x, y, z
using library showing x, y  # accessible as x, y, but z is hidden
using library hiding z  # x and y accessible, but z is hidden

fun square(x)
    x^2  # functions automatically return the value their last expressions

fun factorial(n)
    if n == 1  # if statements are expressions
        n
    else
	n * factorial(n-1)

# we also have single line functions and if statements
fun factorial2(n) = if n == 1 then n else n * factorial2(n-1)

square2 = x => x^2  # we also have lambdas

fun fit_model(train_x, train_y, ?test_x, ?test_y, l1_re = 0, l2_reg = 0, grad_desc = true, alpha = 0.01)
    # complicated implementation goes here
    # test_x and test_y are optional
    # the remaining parameters are keyword parameters with default values

fit_model_to_data = fit_model[train_x, train_y, test_x, test_y]  # square brackets denote partial function application
fit_model_to_data(l1_re = 0.3, alpha = 0.001)  # now we've specified the data so we only need to pass hyperparameters (optionally)
fit_model_to_data()  # we can also omit all arguments since there are default hyperparameters in the function signature

class Person
    fun Person(name, age, occupation = ~student)
        @name = name  # variables preceeded by @ are instance variables
        @age = age
        @occupation = occupation  # occupation is a symbol

    fun first_name  # functions that take no arguments can be declared without parentheses
        @age.split(' ').head
    
    fun birthday!  # by convention, functions that mutate state end in exclamation points
        @age += 1

    fun is_major?  # likewise boolean functions typically end with question marks
        @age >= 18

steve = Person("Steve Higgins", 17)
# functions declared without parentheses must still be called with parentheses though
print(steve.first_name())  # => Steve
steve.birthday!()

# classes support operator overloading
class Complex
    fun Complex(re, im)
        @re = re
        @im = im

    fun +(that)
        Complex(@re + that.re, @im + that.im)

    fun *(that)
        Complex(@re * that.re - @im * that.im, @re * that.im + @im * that.re)

# having to manually assign instance variables to parameters seems redundant; let's make a new type of class

using reflection showing defclass
import lexemes as L  # lexemes is a collection of lexemes that can be used to match tokens
import models as M  # models is a collection of semantic models (i.e. grammars that have been parsed and preprocessed)

# keyword takes two arguments, though the second is optional and the first may be the empty grammar
# the first argument is a model for the declarator, the string that comes immediately after a keyword on the same line (e.g. a function name and parameter list)
# the second argument is a model for the block indented below a keyword (e.g. a function implementation)
# when a keyword is invoked, the function defined here is called with ASTs for the declarator and the block
# many grammars are defined in the macros module, and many have built-in preprocessing (like the class_body grammar)
keyword record(name: L.name, header: M.class_header, body: M.class_body)
    # the $() syntax quotes the contents, parsing the result to an AST
    # this is just shorthand for the quote() macro
    # & unquotes the symbol that follows and pastes the string that it refers to from outer scope
    body.constructor.statements.prepend($(@&param = &param) for param in body.constructor.parameters)
    defclass(name, body)  # this registers the class globally (it could also be registered locally with defclass_local)

# now we can declare our person class like this
record Person
    fun Person(name, age, occupation = ~student)

    fun first_name
        @age.split(' ').head
    
    fun birthday!
        @age += 1

    fun is_major?
        @age >= 18

import grammars as G showing grammar

# now let's make a function keyword that checks the types of its arguments at runtime
grammar
    param = name:L.name (':' type:L.name)?
    typed_signature = L.name '(' G.delimited(param, ',') ')'

# where delimited might be defined
fun delimited(sub, delim)
    delimited_elems = grammar (head:sub tail:(delim sub)*)?  # here we're using the grammar macro, which works much the same way as the grammar keyword
    grammar elems:delimited_elems =>  # if grammar is passed a function, it makes a grammar that matches the type of the argument and makes a model by running the function on it
        if elems.head  # checks for nil
            [elems.head] + elems.tail
        else
            []

keyword tfun(signature: typed_signature, body: M.function_body)
    typed_params = signature.parameters.filter(p => p.type)
    body.prepend($(if &(param).type != &(param.type) then  # checks if param.type isn't nil
                   throw TypeError("Parameter &param is of type #{&(param).type}, but &(param.type) was expected"))
                 for param in typed_params)
    # note that in quote() or $() form, the statement is collapsed to a single line before parsing
    # to use a multiline quote, use a quote block, like this
    ###
    quote
        if &(param).type != &(param.type)
            throw TypeError("Parameter &param is of type #{&(param).type}, but &(param.type) was expected")
    ###


# we can also make a keyword that only uses grammars, not models, in which case we have to do all processing ourselves
# that includes (optionally) recursively running the keyword and macro parser on any keywords or macros we want to be available within this block

# we also have traditional macros that return code that is then evaluated at the invocation site
macro debug(...vars)  # in functions and macros, this is how variable arity is denoted
    concat($(print("&var = #{&var}")) for var in vars)

# now we can use debug like this
x = 5
y = 10
debug(x, y)  # => x = 5\ny = 10

# macros and functions that take arguments (but not functions that take no arguments) can be invoked without parentheses, so the above could also be written as
debug x y

# we can also locally override literal syntax:
literal array_brackets [elems] = Array(...elems)

# now to use this syntax, we have two options
using array_brackets  # this will use array_brackets literals until overridden by another using statement
x = [1, 2, 3]
using list_brackets
y = [1, 2, 3]  # x is an array but y is a list (the default type of brackets literals)

with array_brackets  # with statements only put the change into effect in their bodies
    x = [1, 2, 3]
y = [1, 2, 3]  # likewise x and y have different types

# now that we have a language with relatively extensive metaprogramming support, we can see that making a generative programming library is quite elegant
# first let's see what the user api might look like

using python

def square(x)  # function syntax is identical except the def keyword is now used instead of fun
    x^2
# square is now a python function Function(params = [x], body = PwrExpr(base = x, exponent = 2))

object Person  # likewise class syntax with the object keyword
    def Person(age, name)
        @age = age
        @name = name

# to make a program, we must compose expressions
with pybrackets
    x = [1, 2, 3, 4, 5]  # this is a python expression ListLiteral(elems = [1, 2, 3, 4, 5])
y = x.map(lambda a => a + 2)  # this is a python expression Map(list = ListLiteral(elems = [1, 2, 3, 4, 5]),
                              #                                 function = Function(params = [a], body = AddExpr(args = [a, 2])))
# note that the function in the map expression is a python function, not an obsidian function
z = y.map(square)  # this is a python expression Map(Map(...), function = Function(params = [x], body = PwrExpr(base = x, exponent = 2)))

# at the end of the day, we want to produce some side effects, and for that we need procedures
proc print_z
    print(z)  # within proc, functions always refer to python functions; you can't use obsidian functions within proc; thus print is python's print function

# if we want to produce a python program out of a proc, we can use the compile function
program = compile(print_z)
print(program)  # this is obsidian's print function again, since we're out of a proc context
# this will output something like the following
###
print(map(map([1, 2, 3, 4, 5], lambda x: x + 2), lambda x: x**2))
###

# we can make expressions representing the instantiation of python objects
steve = Person(age = 3, name = "Steve")  # this is a python expression ObjectExpr(type = :Person, attrs = {:age: 3, :name: "Steve"})
steve.age = 4  # ERROR! because this is an imperative action, we can't actually write this outside of a proc; instead we can do this
# note that ObjectExpr has the dot operator overloaded to make sure that throws an error at runtime (which is compile time for the python program)
proc happy_birthday
    steve.age = 4

# nothing prevents us from using the same expression to generate more than one new expression, and then to use both of those in a proc

x = pyint(3)  # this is a python expression IntExpr(3)
y = x * 2  # this is a python expression MulExpr(args = [IntExpr(3), 2])
z = x - 1  # this is a python expression AddExpr(args = [IntExpr(3), -1])
proc compute_y_z
    print(y)
    print(z)
# because in obsidian the IntExpr(3) in y and z are actually the same object, we can examine the graph of compute_y_z
print(compute_y_z.children())  # => {MulExpr(args = [IntExpr(3), 2]), AddExpr(args = [IntExpr(3), -1])}
print(flatten({c.children() for c in compute_y_z.children()}))  # => {IntExpr(3)}
# note that it is only because we are using a set (the {} syntax) that this last command gives a single element; the following gets a different result
print(flatten([p.children() for p in compute_y_z.children()]))  # => [IntExpr(3), IntExpr(3)]

# the python module provides several helper functions to facilitate examining the computational graph
print(compute_y_z.leaves())  # => {IntExpr(3)}
print(compute_y_z.multileaves())  # {IntExpr(3)}
# multileaves finds all the leaves of the graph that have multiple parents
# this is useful if you want to avoid duplicate computation
compute_y_z.trim(IntExpr(3), Reference(:x))  # the trim function replaces a leaf with the provided node and marks it as trimmed
# now suppose we were building up some python code in the compile function
# if we find a multileaf, we might want to make it a separate variable and trim it to a reference
print(compute_y_z.leaves())  # => {MulExpr(args = [Reference(:x), 2]), AddExpr(args = [Reference(:x), -1])}
# the leaves function only looks at untrimmed nodes, so now the leaves show those nodes that depended on the previous layer of leaves
print(compute_y_z.multileaves())  # => {}
print(compute_y_z.unileaves())  # => {MulExpr(args = [Reference(:x), 2]), AddExpr(args = [Reference(:x), -1])}
compute_y_z.collapse(compute_y_z.unileaves())  # this trims every node in a set to itself
compute_y_z.leaves()  # => {Proc(statements = [PrintStmt(MulExpr(args = [Reference(:x), 2])), AddExpr(args = [Reference(:x), -1])])}
# you can see how by iteratively assigning multileaves to variables, trimming them to references, then collapsing strings of unileaves 
# we can build up a python code that efficiently executes a procedure

# there are two incredibly powerful aspects of generative programming
# 1. we can build up programs programmatically
# 2. we can verify program correctness at compile time *in the language that we're coding in*
# the first aspect isn't too different from what macros allow us to do
# the second is much harder to achieve without generative programming
# it allows us to, for example, make sure that users invoke a library we've written correctly

module websockets
    object Websocket
        # some implementation goes here
        def initialize!()
            # some more implementation
        def open!()
            # we want to make sure initialize is called exactly once, and before open
        # etc.
    
    fun verify(prog) = assert all $ prog.filter(match MethodCall(object = Websocket, name = :open!)).map call =>
        prog.prune_after(call).contains_one(match MethodCall(object = call.object, name = :initialize!))

# now if we have a program, we can make sure that it matches that specification
import websockets as ws
socket = Websocket(...)
proc connect_and_send
    socket.open!()
    socket.send!("Hello, world!")

verify(connect_and_send)  # => ERROR!
program = compile(connect_and_send)  # won't run

# in practice, we use keywords that automatically compile, save, and verify our programs according to the libraries they've used

module websockets
    ...
    hide fun verify(prog) = ...
    register_verification(verify)
        
import websockets as ws
socket = Websocket(...)
proc connect_and_send
    socket.open!()
    socket.send!("Hello, world!")
main
    connect_and_send()

# main will treat its contents as the body of a proc, verify it according to all verifications that have been registered by imports, and compile it to a file with the same basename as the source file (and a .py extention instead of .on)

# of course, manually walking the whole program tree to verify something simple like that is overkill
# this works much more straightforwardly:

module websockets
    object Websocket
        @@initialized = false  # the @@ operator accesses attributes of the expression object that represents the instantiated websocket
        # some implementation goes here
        def initialize!()
            if not guarantee(not @@initialized)  # @@initialized can be an expression representing dependency on other values
                # guarantee tries to prove that the statement will be true and returns false if it can't (or if it can prove the inverse)
                throw Error("Websocket might already be initialized!")
            # some more implementation
        def open!()
            if not guarantee(@@initialized)
                throw Error("Websocket might not be initialized!")


# in the same way, we can make sure we never call head() on an empty list
module list
    object List
        @@length = 0
        def append!()
            @@length += 1
            ...
        def head()
            if not guarantee(@@length > 0)
                throw Error("Length not guaranteed to be positive!")


# generative programming makes a lot of sense for web programming, where programs are compiled to multiple languages (but still written solely in obsidian) and verification can go beyond type checking
# it also makes sense in a deep learning context, where programs that are compiled to a single cuda file and compiled with nvcc will be significantly faster than those constructed in python and hindered by python's slow loops
```
