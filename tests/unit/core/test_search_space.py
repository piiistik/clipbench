from clipbench.core.search_space import (
    Evaluation,
    SearchSpace,
    SpaceDefinition,
    VariableVector,
)


def test_search_space_type_aliases_are_importable():
    vector: VariableVector = (1, 2)
    evaluation: Evaluation = 1.5
    space: SearchSpace = {vector: evaluation}
    definition: SpaceDefinition = ((0, 3), (0, 4))

    assert space[(1, 2)] == 1.5
    assert definition[1] == (0, 4)
