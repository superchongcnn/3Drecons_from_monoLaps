# 6. Main execution script
# main.py

import numpy as np
from src.config import Config
from src.image_acquisition import ImageAcquisition
from src.feature_extraction import FeatureExtractor
from src.camera_pose import CameraPoseEstimator
from src.reconstruction import Reconstructor
import open3d as o3d

def main():
    # Initialize configuration
    config = Config()

    # Initialize components
    image_acquirer = ImageAcquisition(config)
    feature_extractor = FeatureExtractor(config)
    pose_estimator = CameraPoseEstimator(config)
    reconstructor = Reconstructor(config)

    # Load and preprocess images
    images = image_acquirer.load_images(config.RAW_IMAGES_DIR)
    processed_images = [image_acquirer.preprocess_image(img) for img in images]

    # Extract features from all images
    all_keypoints = []
    all_descriptors = []
    for img in processed_images:
        kp, desc = feature_extractor.detect_and_compute(img)
        all_keypoints.append(kp)
        all_descriptors.append(desc)

    # Initialize 3D reconstruction
    points_3d = []
    camera_poses = [(np.eye(3), np.zeros((3, 1)))]  # First camera is at origin

    # Process image pairs
    for i in range(len(images) - 1):
        # Match features between consecutive images
        matches = feature_extractor.match_features(all_descriptors[i], all_descriptors[i + 1])

        # Estimate camera pose
        R, t, mask = pose_estimator.estimate_pose(
            all_keypoints[i], all_keypoints[i + 1],
            matches, config.CAMERA_MATRIX
        )
        camera_poses.append((R, t))

        # Triangulate points
        new_points = reconstructor.triangulate_points(
            config.CAMERA_MATRIX,
            camera_poses[i][0], camera_poses[i][1],
            camera_poses[i+1][0], camera_poses[i+1][1],
            all_keypoints[i], all_keypoints[i + 1],
            matches
        )
        points_3d.extend(new_points)

    # Create and process point cloud
    pcd = reconstructor.create_point_cloud(np.array(points_3d))
    
    # Surface reconstruction
    mesh = reconstructor.surface_reconstruction(pcd)

    # Visualization
    o3d.visualization.draw_geometries([mesh])

if __name__ == "__main__":
    main()
