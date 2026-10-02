cd('/mnt/data/BRPHM/rul-space/work/f1_generator_20261002_leo600_v1/sim');
env_summary = make_dataset('Line', 'both', 'Workers', 1, 'EnvCheck', true, ...
    'OutRoot', '/mnt/data/BRPHM/rul-space/work/f1_generator_20261002_leo600_v1/generated');
disp(env_summary);
dry_summary = make_dataset('Line', 'both', 'Workers', 1, 'DryRun', true, ...
    'OutRoot', '/mnt/data/BRPHM/rul-space/work/f1_generator_20261002_leo600_v1/generated');
disp(dry_summary);
