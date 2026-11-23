"""Round 17: bounded (capacity two) additive contexts over 36 typed products.

This is an explicit FINITE partial algebra, not a new founding axiom.
The full A×B receipts survive every C-sum and every C×D / E×F product.
The two-term cap is a stated experimental restriction; no implicit zero result.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product, combinations_with_replacement
from collections import deque, defaultdict

A_VALUES = (-3, -2, -1, 1, 2, 3)
B_VALUES = (-6, -3, -2, 2, 3, 6)
D_READINGS = {'seal':2,'inspect':3,'homA':5,'homB':7}

@dataclass(frozen=True)
class V:
    sort: str
    name: str
    amount: int
    inputs: tuple['V',...] = ()

@dataclass(frozen=True)
class Op:
    name: str
    signatures: tuple[str,...]
    output: str
    table: dict[tuple[V,...],V]

@dataclass(frozen=True)
class Hole:
    op: str
    pos: int
    fixed: tuple[V|None,...]
    def describe(self):
        return f"{self.op}("+', '.join('□' if x is None else x.name for x in self.fixed)+')'

@dataclass(frozen=True)
class Witness:
    kind: str
    steps: tuple[Hole,...]
    left_end: V|None
    right_end: V|None

class Model:
    def __init__(self, small=False, include_source_probes=True):
        aa = (-3,3) if small else A_VALUES
        bb = (-2,2) if small else B_VALUES
        self.A = tuple(V('A',f'A_{a}',a) for a in aa)
        self.B = tuple(V('B',f'B_{b}',b) for b in bb)
        self.D = tuple(V('D',name,reading) for name,reading in D_READINGS.items()
                       if include_source_probes or name in ('seal','inspect'))
        self.F = (V('F','confirm',5),)
        self.atoms = tuple(V('C',f'C_({a.amount},{b.amount})',a.amount*b.amount,(a,b))
                           for a,b in product(self.A,self.B))
        self.empty = V('C','0_C',0)
        self.doubles = tuple(V('C',f'[{a.name}+{b.name}]',a.amount+b.amount,(a,b))
                             for a,b in combinations_with_replacement(self.atoms,2))
        self.C = (self.empty,)+self.atoms+self.doubles
        self.terms={self.empty:()}
        self.terms.update({c:(c,) for c in self.atoms})
        self.terms.update({c:c.inputs for c in self.doubles})
        self.cbyterms={t:c for c,t in self.terms.items()}
        first={(c.inputs):c for c in self.atoms}
        # Addition is defined only if resulting term multiplicity <= 2.
        added = {}
        for x in self.C:
            added[(self.empty,x)]=x
            added[(x,self.empty)]=x
        for x,y in product(self.atoms,repeat=2):
            terms=tuple(sorted((x,y),key=self.atoms.index))
            added[(x,y)]=self.cbyterms[terms]
        second={};ee=[]
        for c,d in product(self.C,self.D):
            ts=self.terms[c]
            if not ts:continue
            A={p.inputs[0].amount for p in ts}
            B={p.inputs[1].amount for p in ts}
            allowed=(
                (d.name=='seal' and len(A)==1 and all(b%2==0 for b in B)) or
                (d.name=='inspect' and len(B)==1 and all(a%2==0 for a in A)) or
                (d.name=='homA' and len(A)==1) or
                (d.name=='homB' and len(B)==1)
            )
            if allowed:
                e=V('E',f'E[{c.name},{d.name}]',c.amount*d.amount,(c,d))
                second[c,d]=e;ee.append(e)
        self.E=tuple(ee)
        third={};gg=[]
        for e,f in product(self.E,self.F):
            c,d=e.inputs
            if d.name=='seal' and {t.inputs[0].amount for t in self.terms[c]}=={1}:
                g=V('G',f'G[{e.name},confirm]',e.amount*f.amount,(e,f))
                third[e,f]=g;gg.append(g)
        self.G=tuple(gg)
        self.sorts={'A':self.A,'B':self.B,'C':self.C,'D':self.D,'E':self.E,'F':self.F,'G':self.G}
        self.ops=(Op('mul_AB',('A','B'),'C',first),Op('add_CC',('C','C'),'C',added),
                  Op('mul_CD',('C','D'),'E',second),Op('mul_EF',('E','F'),'G',third))
        self.byname={o.name:o for o in self.ops}
        self.all=tuple(v for arr in self.sorts.values() for v in arr)
        self.index={v:i for i,v in enumerate(self.all)}
        self._contexts={s:self.contexts_for(s,True) for s in self.sorts}
        self._full_contexts={}
        self._contexts_checked=False

    def contexts_for(self,sort,reduced=True):
        result=[]
        for op in self.ops:
            for pos,s in enumerate(op.signatures):
                if s!=sort:continue
                ranges=[]
                for j,other in enumerate(op.signatures):
                    if j==pos:ranges.append((None,))
                    elif reduced and op.name=='add_CC':
                        # Lemma: a sum by 2 atoms can be decomposed into sequential
                        # sums by each atom, with identical definedness and result.
                        ranges.append((self.empty,)+self.atoms)
                    else:ranges.append(self.sorts[other])
                for args in product(*ranges):
                    result.append(Hole(op.name,pos,args))
        return tuple(result)

    def step(self,x,hole):
        op=self.byname[hole.op]
        args=tuple(x if i==hole.pos else fixed for i,fixed in enumerate(hole.fixed))
        return op.table.get(args)

    def atom(self,a,b):
        return next(v for v in self.atoms if v.inputs[0].amount==a and v.inputs[1].amount==b)

    def sum(self,x,y):
        return self.byname['add_CC'].table.get((x,y))

    def old_key(self,c):
        a,b=c.inputs[0].amount,c.inputs[1].amount
        return (c.amount,b%2==0,a%2==0,(b%2==0 and a==1))

    def semantic_double_key(self,c):
        p,q=c.inputs
        a,b=p.inputs[0].amount,p.inputs[1].amount
        aa,bb=q.inputs[0].amount,q.inputs[1].amount
        homo_a=a==aa;homo_b=b==bb
        seal=homo_a and b%2==0 and bb%2==0
        inspect=homo_b and a%2==0 and aa%2==0
        return (c.amount,homo_a,homo_b,seal,inspect,seal and a==1)

    def public_key(self,c):
        if c==self.empty: return ('empty',0)
        if c in self.atoms:return ('atom',c.name)
        return ('double',self.semantic_double_key(c))

    def refine_fast(self,reduced=True):
        cx=self._contexts if reduced else {s:self.contexts_for(s,False) for s in self.sorts}
        names={}; blocks={}
        for x in self.all:
            key=(x.sort,x.amount)
            if key not in names:names[key]=len(names)
            blocks[x]=names[key]
        rounds=0
        while True:
            names={}; nxt={}
            for x in self.all:
                key=(blocks[x],tuple(-1 if (out:=self.step(x,h)) is None else blocks[out]
                                     for h in cx[x.sort]))
                if key not in names:names[key]=len(names)
                nxt[x]=names[key]
            if len(names)==len(set(blocks.values())):
                return nxt,rounds
            blocks=nxt;rounds+=1
            if rounds > len(self.all):raise AssertionError('No convergence')

    def valid_for_all_contexts(self,blocks):
        # Independent unpruned one-hole condition checked by direct witnesses.
        for sort,vals in self.sorts.items():
            groups=defaultdict(list)
            for x in vals:groups[blocks[x]].append(x)
            for h in self.contexts_for(sort,reduced=False):
                for group in groups.values():
                    outcome={-1 if (out:=self.step(x,h)) is None else blocks[out]
                             for x in group}
                    if len(outcome)>1:return sort,h,group,outcome
        return None

    def witness(self,x,y,reduced=True,max_states=200000):
        if x.sort!=y.sort:raise ValueError('Only one sort can be compared')
        cx=self._contexts if reduced else {s:self.contexts_for(s,False) for s in self.sorts}
        queue=deque([(x,y,())]);seen={(x,y)};pending=None
        while queue:
            a,b,path=queue.popleft()
            if a.amount!=b.amount:return Witness('observation',path,a,b)
            if pending is not None and len(path)>=len(pending.steps):return pending
            for h in cx[a.sort]:
                aa,bb=self.step(a,h),self.step(b,h)
                if (aa is None)!=(bb is None):
                    if pending is None:pending=Witness('definedness',path+(h,),aa,bb)
                elif aa is not None and (aa,bb) not in seen:
                    seen.add((aa,bb));queue.append((aa,bb,path+(h,)))
            if len(seen)>max_states:raise RuntimeError('Bounded BFS limit')
        return pending


def previous_verifier_adapter(model:Model):
    """Reuse the round-16 many-sorted verifier without replacing its API.

    Its generic binary-operation tables stay complete. For large capacity-two
    models we select generator-addition contexts for the fast refinement; the
    independent all-context check verifies the quotient against the FULL table.
    """
    from typed_context_verifier import FiniteSortedAlgebra, Operation
    old_ops=tuple(Operation(o.name,o.signatures,o.output,o.table) for o in model.ops)
    algebra=FiniteSortedAlgebra(model.sorts,old_ops,lambda x:x.amount)
    algebra.contexts['C']=tuple(
        h for h in algebra.contexts['C']
        if h.operation!='add_CC' or (
            h.arguments[1-h.position]==model.empty or
            h.arguments[1-h.position] in model.atoms
        )
    )
    return algebra


def summarize(m:Model,blocks):
    return {s:len({blocks[x] for x in vals}) for s,vals in m.sorts.items()}

if __name__=='__main__':
    model=Model()
    blocks,rounds=model.refine_fast()
    print('full states',len(model.all),'rounds',rounds)
    print('quotient',summarize(model,blocks))
    print('old singleton quotient',len({model.old_key(x) for x in model.atoms}))
    print('new singleton quotient',len({blocks[x] for x in model.atoms}))
    print('double semantic profiles',len({model.semantic_double_key(x) for x in model.doubles}))
    x,y,z=model.atom(3,2),model.atom(-3,-2),model.atom(3,2)
    print('witness',model.witness(x,y))
