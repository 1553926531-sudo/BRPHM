cd('/mnt/data/BRPHM/rul-space/work/f1_generator_20261002_v12_s920/sim');
summary = make_dataset('Line', 'rwa', 'Workers', 1, 'SimMode', 'accelerator', 'Smoke', false, 'MaxAttempts', 1, 'OutRoot', '/mnt/data/BRPHM/rul-space/work/f1_generator_20261002_v12_s920/generated');
disp(summary);
