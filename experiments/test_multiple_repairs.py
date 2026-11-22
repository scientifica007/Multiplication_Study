"""Independent finite verification of multi-repair contextual equivalence."""
import unittest
from itertools import product
from multiple_repairs import (
    Repair, State, alphabet, common_periods, contextual_key, distinguishing_word,
    minimization, predicted, reachable, repair_signature_periods, total_repair,
    transition, observable
)


def partial_maps(m):
    # for each input, choose disabled (-1) or the desired output 0...m-1
    for outputs in product(range(-1,m),repeat=m):
        values=tuple(max(x,0) for x in outputs)
        domain=tuple(x>=0 for x in outputs)
        yield Repair('r',values,domain)


class MultiRepairTests(unittest.TestCase):
    def assert_matches(self,N,h,m,repairs,check_pairs=False):
        states, classes=minimization(N,h,m,repairs)
        self.assertEqual((len(states),len(set(classes.values()))), predicted(N,h,m,repairs))
        self.assertEqual(common_periods(m,repairs),repair_signature_periods(m,repairs))
        if check_pairs:
            keys={s:contextual_key(s,h,m,repairs) for s in states}
            for i,s in enumerate(states):
                for t in states[i:]:
                    self.assertEqual(keys[s]==keys[t], classes[s]==classes[t],
                                     (N,h,m,repairs,s,t))

    def test_intersection_of_two_total_repairs_mod_6(self):
        m=6; N=3; h=2
        rho2=total_repair('mod2',tuple(x%2 for x in range(m)))
        rho3=total_repair('mod3',tuple(x%3 for x in range(m)))
        self.assertEqual(common_periods(m,(rho2,)),(0,2,4))
        self.assertEqual(common_periods(m,(rho3,)),(0,3))
        self.assertEqual(common_periods(m,(rho2,rho3)),(0,))
        self.assertEqual(predicted(N,h,m,(rho2,)),(187,91))
        self.assertEqual(predicted(N,h,m,(rho3,)),(187,115))
        self.assertEqual(predicted(N,h,m,(rho2,rho3)),(187,187))
        self.assert_matches(N,h,m,(rho2,rho3),True)

    def test_partial_domain_counterexample_constant_reset(self):
        m=6;N=3;h=2
        even=Repair('even',(0,)*m,tuple(x%2==0 for x in range(m)))
        naive=total_repair('total',(0,)*m)
        self.assertEqual(common_periods(m,(naive,)),tuple(range(m)))
        self.assertEqual(common_periods(m,(even,)),(0,2,4))
        self.assertEqual(predicted(N,h,m,(naive,)),(187,67))
        self.assertEqual(predicted(N,h,m,(even,)),(187,91))
        self.assert_matches(N,h,m,(even,),True)
        s=State(((0,1),(1,1)),0,True)
        t=State(((0,1),(1,1)),1,True)
        self.assertEqual(distinguishing_word(s,t,N,h,m,(even,)),('repair:even',))
        u=State(((0,1),(1,1)),2,True)
        self.assertIsNone(distinguishing_word(s,u,N,h,m,(even,)))

    def test_all_partial_maps_small_moduli(self):
        count=0
        for m in (1,2,3):
            for repair in partial_maps(m):
                self.assert_matches(2,1,m,(repair,),False)
                count+=1
        self.assertEqual(count,2+9+4**3)  # 75 total partial maps

    def test_all_ordered_pairs_partial_maps_mod2(self):
        maps=list(partial_maps(2))
        count=0
        for i,x in enumerate(maps):
            for j,y in enumerate(maps):
                a=Repair('first',x.values,x.domain)
                b=Repair('second',y.values,y.domain)
                self.assert_matches(2,1,2,(a,b),False)
                count+=1
        self.assertEqual(count,81)

    def test_all_total_pairs_mod3(self):
        m=3
        maps=list(product(range(m),repeat=m))
        for i,x in enumerate(maps):
            for j,y in enumerate(maps):
                self.assert_matches(2,1,m,(total_repair('x',x),total_repair('y',y)))
        self.assertEqual(len(maps)**2,729)

    def test_nontrivial_independent_partial_pairs_mod4(self):
        m=4
        r1=Repair('even',(0,)*m,(True,False,True,False))
        r2=Repair('odd',(0,)*m,(False,True,False,True))
        self.assertEqual(common_periods(m,(r1,r2)),(0,2))
        self.assert_matches(3,2,m,(r1,r2),True)
        r3=Repair('index3',(0,1,0,0),(True,True,False,True))
        self.assert_matches(3,2,m,(r1,r2,r3),True)

    def test_forbidden_window_and_invalid_events(self):
        m=3;rho=total_repair('fix',(0,)*m); repairs=(rho,)
        start=State((),0,False)
        self.assertIsNone(transition(start,'repair:fix',3,2,m,repairs))
        s=transition(start,(0,-1),3,2,m,repairs)
        s=transition(s,(1,1),3,2,m,repairs)
        self.assertIsNone(transition(s,'repair:fix',3,2,m,repairs))
        s=transition(s,(2,1),3,2,m,repairs)
        self.assertIsNotNone(transition(s,'repair:fix',3,2,m,repairs))
        self.assertIsNone(transition(s,(2,1),3,2,m,repairs))
        with self.assertRaises(ValueError):transition(start,(0,0),3,2,m,repairs)
        with self.assertRaises(ValueError):transition(start,'repair:unknown',3,2,m,repairs)

    def test_separator_agrees_with_exact_partition_selected_models(self):
        for N,h,m,rho in ((2,1,3,(total_repair('m',(0,0,0)),)),
                          (2,1,3,(total_repair('m',(0,0,1)),)),
                          (2,1,4,(Repair('even',(0,)*4,(True,False,True,False)),))):
            states,classes=minimization(N,h,m,rho)
            for i,s in enumerate(states):
                for t in states[i:]:
                    self.assertEqual(distinguishing_word(s,t,N,h,m,rho) is None,
                                     classes[s]==classes[t])


if __name__=='__main__':unittest.main()
