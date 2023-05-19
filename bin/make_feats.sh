#!/bin/bash

if [[ $# -lt 1 ]];then
  echo "make_feats <base_dir>"
  exit;
fi;

BASE_DIR=`realpath $1`
CORPUS_NAME=${BASE_DIR##*/}
if [ ! -d $BASE_DIR ]; then
  echo "$BASE_DIR does not exist"
fi;

echo $BASE_DIR
echo $CORPUS_NAME

FEATS_FILES=`find "$BASE_DIR/$CORPUS_NAME" -name "feats.1.*.scp"`
for feat_file in $FEATS_FILES; do
  echo $feat_file
  task_id=${feat_file#*feats.}
  task_id=${task_id%.scp}
  echo $task_id
  trfeat_arks="trfeats.${task_id}.ark"
  trfeat_scps="trfeats.${task_id}.scp"
  gmmlik_path="gmmlik.${task_id}.ark"
  boost_path="boost.${task_id}.mdl"
  
  echo "Generating $trfeat_file"

  splice-feats \
    --left-context=3 --right-context=3 \
    scp,s,cs:"$feat_file" ark:- | \
    transform-feats "$BASE_DIR/alignment/lda.mat" \
      ark:- ark,scp:"$BASE_DIR/alignment/$trfeat_arks,$BASE_DIR/alignment/$trfeat_scps"
  
  break
  # echo "Generating $gmmlik_path"
      
  # gmm-compute-likes \
  #   $BASE_DIR/alignment/$boost_path \
  #   ark:"$BASE_DIR/alignment/$trfeat_file" \
  #   ark:"$BASE_DIR/alignment/$gmmlik_path"
done;

