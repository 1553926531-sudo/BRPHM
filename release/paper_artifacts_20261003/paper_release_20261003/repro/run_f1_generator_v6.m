cd('/mnt/data/BRPHM/rul-space/work/f1_generator_20261001_v6/sim');
% The MATLAB stdout/stderr is redirected by the shell wrapper.  This entry
% point emits only the normal summary; acceptance is based on exit status and
% file-level hashes, never on semantic Tf/code values from stdout.
summary = make_dataset('Line', 'both', 'Workers', 1, 'SimMode', 'accelerator', ...
    'Smoke', false, 'MaxAttempts', 1, ...
    'OutRoot', '/mnt/data/BRPHM/rul-space/work/f1_generator_20261001_v6/generated');
disp(summary);
