cd('/mnt/data/BRPHM/rul-space/work/f1_generator_20261001_v6b/sim');
% stdout/stderr is redirected by the shell wrapper; acceptance uses only
% process status and file-level hashes, never semantic Tf/code output.
summary = make_dataset('Line', 'both', 'Workers', 1, 'SimMode', 'accelerator', ...
    'Smoke', false, 'MaxAttempts', 1, ...
    'OutRoot', '/mnt/data/BRPHM/rul-space/work/f1_generator_20261001_v6b/generated');
disp(summary);
