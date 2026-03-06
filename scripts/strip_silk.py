"""Strip all silkscreen graphics from a KiCad PCB file via text processing."""
import sys


def strip_silk(board_path: str) -> None:
    with open(board_path, 'r') as f:
        lines = f.readlines()

    output = []
    skip_depth = 0
    in_silk_block = False
    block_start_depth = 0
    paren_depth = 0
    block_lines = []
    removed = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check if this line starts an fp_line/fp_arc/fp_circle/fp_poly/fp_rect
        if not in_silk_block and any(stripped.startswith(f'(fp_{t}') for t in ('line', 'arc', 'circle', 'poly', 'rect')):
            # Collect the entire block to check for SilkS
            block_lines = [line]
            depth = 0
            for ch in line:
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
            j = i + 1
            while depth > 0 and j < len(lines):
                block_lines.append(lines[j])
                for ch in lines[j]:
                    if ch == '(':
                        depth += 1
                    elif ch == ')':
                        depth -= 1
                j += 1

            # Check if this block is on a silk layer
            block_text = ''.join(block_lines)
            if '"F.SilkS"' in block_text or '"B.SilkS"' in block_text:
                removed += 1
                i = j
                continue

            # Not silk — keep it
            output.extend(block_lines)
            i = j
            continue

        output.append(line)
        i += 1

    with open(board_path, 'w') as f:
        f.writelines(output)

    print(f"  Stripped {removed} silk graphic elements")


if __name__ == "__main__":
    strip_silk(sys.argv[1])
