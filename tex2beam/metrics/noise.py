import numpy as np

from tex2beam import utils


def swap_random_elements(elements: list, n: int = 1, seed: int = None) -> list:
    """Swap n random elements in a list."""
    rng = np.random.default_rng(seed=seed)
    elements = utils.remove_duplicates(elements)
    if len(elements) <= n:
        return elements
    for _ in range(n):
        i, j = rng.choice(
            range(len(elements)),
            2,
            replace=False,
        )
        elements[i], elements[j] = elements[j], elements[i]
    return elements


def remove_random_elements(
    elements: list, n: int = 1, seed: int = None
) -> list:
    """Remove n random elements from a list."""
    rng = np.random.default_rng(seed=seed)
    elements = utils.remove_duplicates(elements)
    if len(elements) <= n:
        return elements
    for _ in range(n):
        i = rng.choice(range(len(elements)))
        elements.pop(i)
    return elements


def replace_random_elements(
    elements: list, replacements: list, n: int = 1, seed: int = None
) -> list:
    """Replace random element of a list with a random element from another
    list."""
    rng = np.random.default_rng(seed=seed)
    elements = utils.remove_duplicates(elements)
    replacements = utils.remove_duplicates(replacements)
    if len(elements) <= n:
        n = len(elements)
    idxs = np.arange(n)
    rng.shuffle(idxs)
    for i in range(n):
        elements[idxs[i]] = replacements[rng.choice(range(len(replacements)))]
    return elements


def reverse_list(elements: list) -> list:
    """Reverse list elements."""
    return elements[::-1]
