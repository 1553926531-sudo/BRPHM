cd('/mnt/data/BRPHM/rul-space/work/f1_generator_20261002_v11_s918/sim');
summary = make_dataset('Line', 'bat', 'Workers', 1, 'SimMode', 'accelerator', 'Smoke', false, 'MaxAttempts', 1, 'OutRoot', '/mnt/data/BRPHM/rul-space/work/f1_generator_20261002_v11_s918/generated');
disp(summary);
