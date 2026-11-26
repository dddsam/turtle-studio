"""Bounded classroom Turtle language. Input is parsed with CPython's Python 3 grammar."""
import ast
import math
import operator
from dataclasses import dataclass


class LessonError(Exception):
    def __init__(self, line, message):
        super().__init__(message)
        self.line = line


@dataclass(frozen=True)
class Motion:
    line: int
    start: tuple
    end: tuple
    heading: float
    turn: float
    draw: bool
    color: str
    width: float
    speed: float
    label: str


OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}
ALIAS = {'fd':'forward','bk':'backward','back':'backward','rt':'right','lt':'left',
         'pu':'penup','up':'penup','pd':'pendown','down':'pendown','width':'pensize',
         'setpos':'goto','setposition':'goto','seth':'setheading','mainloop':'done'}
ARGUMENTS = {'forward':(1,1),'backward':(1,1),'left':(1,1),'right':(1,1),'goto':(2,2),
             'setheading':(1,1),'penup':(0,0),'pendown':(0,0),'pensize':(1,1),
             'pencolor':(1,1),'color':(1,2),'speed':(1,1),'shape':(1,1),'done':(0,0)}


class Program:
    def __init__(self, color_check):
        self.color_check = color_check
        self.variables = {}
        self.names = {'t'}
        self.x = self.y = self.angle = 0.0
        self.down, self.ink, self.width, self.speed = True, '#165440', 4, 4
        self.steps, self.budget = [], 8000

    def fail(self, node, message):
        raise LessonError(getattr(node, 'lineno', 1), message)

    def number(self, value, node):
        if type(value) not in (int,float) or abs(value) > 1000000 or not math.isfinite(value):
            self.fail(node, '这里需要一个不超过一百万的数字。')
        return value

    def value(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str) and len(node.value) < 100: return node.value
            return self.number(node.value, node)
        if isinstance(node, ast.Name):
            if node.id not in self.variables: self.fail(node, '还没有给 '+node.id+' 赋值。颜色名称要加英文引号。')
            return self.variables[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            n=self.number(self.value(node.operand), node)
            return -n if isinstance(node.op,ast.USub) else n
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            a=self.number(self.value(node.left), node)
            b=self.number(self.value(node.right), node)
            try: out=OPS[type(node.op)](a,b)
            except ZeroDivisionError: self.fail(node,'除数不能是 0。')
            return self.number(out,node)
        self.fail(node,'试试数字、变量或加减乘除。')

    def charge(self,node):
        self.budget -= 1
        if self.budget < 0: self.fail(node,'这次重复太多了，把 range 里的数字改小一些。')

    def block(self, statements):
        for node in statements:
            self.charge(node)
            if isinstance(node,ast.Import):
                if any(a.name!='turtle' for a in node.names): self.fail(node,'这个画室可以导入 turtle 画图库。')
                self.names.update(a.asname or 'turtle' for a in node.names)
            elif isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
                name=node.targets[0].id
                if name in self.names or name=='range': self.fail(node,'给数字换一个变量名吧。')
                self.variables[name]=self.value(node.value)
            elif isinstance(node,ast.For):
                it=node.iter
                if not (isinstance(node.target,ast.Name) and isinstance(it,ast.Call) and
                        isinstance(it.func,ast.Name) and it.func.id=='range' and 1<=len(it.args)<=3 and not it.keywords):
                    self.fail(node,'循环可以写成 for i in range(4):')
                vals=[self.value(v) for v in it.args]
                if any(type(v) is not int for v in vals) or (len(vals)==3 and vals[2]==0):
                    self.fail(node,'range 里用整数，第三个数不能为 0。')
                if node.target.id in self.names or node.target.id=='range': self.fail(node,'试试用 i 作循环变量。')
                for n in range(*vals):
                    self.charge(node)
                    self.variables[node.target.id]=n
                    self.block(node.body)
                self.block(node.orelse)
            elif isinstance(node,ast.Expr) and isinstance(node.value,ast.Call):
                call=node.value; f=call.func
                if not (isinstance(f,ast.Attribute) and isinstance(f.value,ast.Name) and f.value.id in self.names):
                    self.fail(node,'海龟指令以 t. 开头，例如 t.forward(100)。')
                if call.keywords: self.fail(node,'把指令的参数按顺序写在括号里。')
                self.command(ALIAS.get(f.attr,f.attr),[self.value(v) for v in call.args],node)
            elif isinstance(node,ast.Pass): continue
            else: self.fail(node,'画室支持海龟指令、变量和 for 循环。点“指令手册”可以看例子。')

    def command(self,cmd,args,node):
        if cmd not in ARGUMENTS: self.fail(node,'找不到 t.'+cmd+'，点“指令手册”看看拼写。')
        lo,hi=ARGUMENTS[cmd]
        if not lo<=len(args)<=hi: self.fail(node,'t.'+cmd+' 括号里的参数个数不对。')
        if cmd in ('pencolor','color'):
            if any(not isinstance(v,str) or not self.color_check(v) for v in args):
                self.fail(node,'颜色可以写成 "red"、"blue"、"purple" 或 "#165440"。')
            self.ink=args[0];return
        if cmd=='shape':
            if args[0]!='turtle': self.fail(node,'这个课堂模板使用 t.shape("turtle")。')
            return
        if cmd=='done':return
        if cmd in ('penup','pendown'):self.down=cmd=='pendown';return
        vals=[self.number(v,node) for v in args]
        if cmd=='pensize':
            if not 0<vals[0]<=100: self.fail(node,'线宽可以选 1 到 100。')
            self.width=vals[0];return
        if cmd=='speed':
            if type(vals[0]) is not int or not 0<=vals[0]<=10: self.fail(node,'速度用 0 到 10 的整数，0 表示立即画完。')
            self.speed=vals[0];return
        x,y,a=self.x,self.y,self.angle
        turn=0; moving=False
        if cmd in ('forward','backward'):
            d=vals[0] if cmd=='forward' else -vals[0]
            x+=d*math.cos(math.radians(a));y+=d*math.sin(math.radians(a));moving=True
            label=('前进' if cmd=='forward' else '后退')+' '+format(vals[0],'g')+' 步'
        elif cmd=='goto': x,y=vals; moving=True;label='移动到指定坐标'
        elif cmd=='setheading':
            turn=(vals[0]-a+180)%360-180;label='调整朝向'
        else:
            turn=vals[0] if cmd=='left' else -vals[0]
            label=('左转' if cmd=='left' else '右转')+' '+format(vals[0],'g')+'°'
        if max(abs(x),abs(y))>1000000:self.fail(node,'画得太远了，把步数改小一些。')
        if len(self.steps)>=2400:self.fail(node,'画笔动作超过 2400 次了，试试少重复几次。')
        self.steps.append(Motion(node.lineno,(self.x,self.y),(x,y),a,turn,moving and self.down,
                                 self.ink,self.width,self.speed,label))
        self.x,self.y,self.angle=x,y,(a+turn)%360


def plan(source,color_check=lambda c:bool(c)):
    if len(source)>32000: raise LessonError(1,'代码有点长，先试一小段吧。')
    try: tree=ast.parse(source)
    except RecursionError: raise LessonError(1,'指令嵌套太深了，先拆成几行。') from None
    except (SyntaxError, ValueError) as e:
        line=getattr(e,'lineno',None) or 1
        message=str(e)
        if isinstance(e,IndentationError): hint='循环里的指令要对齐，通常在前面留 4 个空格。'
        elif "expected ':'" in message:hint='for 循环这一行的末尾需要英文冒号 :'
        elif 'invalid character' in message:hint='括号、引号和冒号请用英文半角符号。'
        else:hint='看看括号和引号是否成对，循环末尾是否有英文冒号。'
        raise LessonError(line,hint) from None
    program=Program(color_check)
    try: program.block(tree.body)
    except RecursionError: raise LessonError(1,'指令嵌套太深了，先拆成几行。') from None
    return program.steps
