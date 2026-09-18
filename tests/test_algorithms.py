import unittest

from core.evaluation import edge_f1, overlap_metrics
from core.preprocessing import strip_python_prompt_noise
from core.workflow import build_dataflow, topological_order


class CoreAlgorithmTests(unittest.TestCase):
    def test_prompt_noise_is_removed_from_copy(self):
        source = '# note\nx = 1\n"""large note"""\ny = x + 1'
        self.assertEqual(strip_python_prompt_noise(source), 'x = 1\ny = x + 1')

    def test_dataflow_has_stable_order(self):
        graph = build_dataflow(['b = a + 1', 'a = 2'])
        # No forward dependency exists when a producer appears later; original
        # statement order is therefore retained by the stable graph algorithm.
        self.assertEqual(topological_order(graph), [0, 1])

    def test_evaluation_metrics(self):
        metrics = overlap_metrics('a = service.load()', 'a = service.load()')
        self.assertEqual(metrics['node_f1'], 1.0)
        self.assertEqual(edge_f1(['a = source', 'b = a + 1'], ['a = source', 'b = a + 1']), 1.0)


if __name__ == '__main__':
    unittest.main()
